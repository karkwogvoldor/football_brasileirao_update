from dataclasses import FrozenInstanceError

import pytest

from brafoot.engine.clock import MatchClock, MatchPeriod
from brafoot.engine.events import (
    EventTimelineViolation,
    MatchEvent,
    MatchEventType,
    validate_event_timeline,
)
from brafoot.engine.matches import MatchSide
from brafoot.engine.zones import FieldLane, FieldThird, FieldZone


def make_event(**overrides) -> MatchEvent:
    values = {
        "sequence": 1,
        "clock": MatchClock(125, MatchPeriod.FIRST_HALF),
        "event_type": MatchEventType.PASS,
        "team_side": MatchSide.HOME,
        "participant_ids": (10, 11),
        "origin_zone": FieldZone(FieldThird.MIDDLE, FieldLane.CENTER),
        "destination_zone": FieldZone(FieldThird.ATTACKING, FieldLane.LEFT),
        "context": "open_play",
        "outcome": "completed",
        "explanation": "O passe conectou o meio ao corredor ofensivo.",
    }
    values.update(overrides)
    return MatchEvent(**values)


# Registra um evento esportivo persistível com os campos semânticos comuns.
def test_match_event_records_common_semantic_fields():
    event = make_event()

    assert event.sequence == 1
    assert event.clock.display == "02:05"
    assert event.event_type is MatchEventType.PASS
    assert event.team_side is MatchSide.HOME
    assert event.participant_ids == (10, 11)
    assert event.origin_zone.code == "middle_center"
    assert event.destination_zone.code == "attacking_left"
    assert event.context == "open_play"
    assert event.outcome == "completed"


# Permite eventos neutros de início e fim de período sem equipe ou jogadores.
@pytest.mark.parametrize(
    "event_type",
    [MatchEventType.PERIOD_START, MatchEventType.PERIOD_END],
)
def test_period_boundary_event_can_be_neutral(event_type):
    event = make_event(
        event_type=event_type,
        team_side=None,
        participant_ids=(),
        origin_zone=None,
        destination_zone=None,
        context=None,
        outcome=None,
    )

    assert event.team_side is None
    assert event.participant_ids == ()


# Rejeita participantes, zonas e códigos esportivos em eventos neutros de período.
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("participant_ids", (10,)),
        ("origin_zone", FieldZone(FieldThird.MIDDLE, FieldLane.CENTER)),
        ("destination_zone", FieldZone(FieldThird.MIDDLE, FieldLane.CENTER)),
        ("context", "open_play"),
        ("outcome", "completed"),
    ],
)
def test_period_boundary_event_rejects_sport_payload(field, value):
    overrides = {
        "event_type": MatchEventType.PERIOD_START,
        "team_side": None,
        "participant_ids": (),
        "origin_zone": None,
        "destination_zone": None,
        "context": None,
        "outcome": None,
    }
    overrides[field] = value

    with pytest.raises(ValueError, match="período"):
        make_event(**overrides)


# Mantém eventos confirmados imutáveis depois de entrarem na timeline.
def test_match_event_is_immutable():
    event = make_event()

    with pytest.raises(FrozenInstanceError):
        event.outcome = "intercepted"


# Rejeita sequências que não sejam inteiros positivos.
@pytest.mark.parametrize("sequence", [0, -1, True])
def test_match_event_requires_positive_integer_sequence(sequence):
    with pytest.raises(ValueError, match="sequência"):
        make_event(sequence=sequence)


# Exige uma equipe para eventos esportivos e neutralidade nos limites de período.
@pytest.mark.parametrize(
    ("event_type", "team_side"),
    [
        (MatchEventType.PASS, None),
        (MatchEventType.PERIOD_START, MatchSide.HOME),
        (MatchEventType.PERIOD_END, MatchSide.AWAY),
    ],
)
def test_match_event_validates_team_for_event_category(event_type, team_side):
    with pytest.raises(ValueError, match="equipe|período"):
        make_event(event_type=event_type, team_side=team_side)


# Rejeita participantes repetidos, não positivos ou armazenados em coleção mutável.
@pytest.mark.parametrize(
    "participant_ids",
    [
        (10, 10),
        (0,),
        (-1,),
        (True,),
        [10, 11],
    ],
)
def test_match_event_requires_unique_positive_participant_tuple(participant_ids):
    with pytest.raises(ValueError, match="participantes"):
        make_event(participant_ids=participant_ids)


# Rejeita zonas livres que não pertencem ao domínio semântico do campo.
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("origin_zone", "middle_center"),
        ("destination_zone", "attacking_left"),
    ],
)
def test_match_event_requires_domain_zones(field, value):
    with pytest.raises(ValueError, match="zona"):
        make_event(**{field: value})


# Rejeita códigos ambíguos e explicações vazias no envelope do evento.
@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("context", " open_play", "contexto"),
        ("outcome", "", "resultado"),
        ("explanation", "   ", "explicação"),
    ],
)
def test_match_event_requires_canonical_codes_and_explanation(field, value, message):
    with pytest.raises(ValueError, match=message):
        make_event(**{field: value})


# Persiste e restaura o evento sem perder tipos ou informações semânticas.
def test_match_event_snapshot_round_trip_is_lossless():
    event = make_event()

    snapshot = event.to_snapshot()

    assert snapshot == {
        "sequence": 1,
        "elapsed_seconds": 125,
        "period": "first_half",
        "event_type": "pass",
        "team_side": "home",
        "participant_ids": [10, 11],
        "origin_zone": "middle_center",
        "destination_zone": "attacking_left",
        "context": "open_play",
        "outcome": "completed",
        "explanation": "O passe conectou o meio ao corredor ofensivo.",
    }
    assert MatchEvent.from_snapshot(snapshot) == event


# Aceita sequências consecutivas e usa a sequência para desempatar o mesmo segundo.
def test_event_timeline_accepts_consecutive_events_at_same_clock():
    events = (
        make_event(sequence=7),
        make_event(sequence=8, event_type=MatchEventType.CARRY),
    )

    assert validate_event_timeline(events) == ()


# Sinaliza lacunas ou repetições na sequência global dos eventos.
@pytest.mark.parametrize("next_sequence", [7, 9])
def test_event_timeline_reports_non_contiguous_sequence(next_sequence):
    violations = validate_event_timeline(
        (make_event(sequence=7), make_event(sequence=next_sequence))
    )

    assert violations == (
        EventTimelineViolation(
            code="non_contiguous_event_sequence",
            event_sequence=next_sequence,
            message="A sequência dos eventos deve avançar de um em um.",
        ),
    )


# Sinaliza quando o relógio de um evento volta para um segundo anterior.
def test_event_timeline_reports_clock_regression():
    violations = validate_event_timeline(
        (
            make_event(sequence=1, clock=MatchClock(200, MatchPeriod.FIRST_HALF)),
            make_event(sequence=2, clock=MatchClock(100, MatchPeriod.FIRST_HALF)),
        )
    )

    assert [violation.code for violation in violations] == [
        "event_clock_moved_backwards"
    ]


# Sinaliza uma regressão de período mesmo quando o segundo acumulado é igual.
def test_event_timeline_reports_period_regression_at_same_clock():
    violations = validate_event_timeline(
        (
            make_event(
                sequence=1,
                clock=MatchClock(2700, MatchPeriod.SECOND_HALF),
            ),
            make_event(
                sequence=2,
                clock=MatchClock(2700, MatchPeriod.HALF_TIME),
            ),
        )
    )

    assert [violation.code for violation in violations] == [
        "event_period_moved_backwards"
    ]
