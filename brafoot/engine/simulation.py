"""Deterministic generation of semantic match events, one segment at a time.

The simulation never touches the interface or the database. It receives two
teams (already reduced to assigned players and their profiles), the persisted
``MatchState`` and a ruleset, and returns the confirmed events together with
the next state. The same input always produces the same output.

Conventions
-----------
* ``MatchState.ball_zone`` is expressed from the perspective of the team in
  possession, as are the origin/destination zones of every event, relative to
  the event's ``team_side``.
* ``team_side`` is the team performing the action. ``participant_ids`` always
  belong to that team, except ``DUEL`` whose second participant is the
  opposing player.
* A completed pass, cross or carry leaves the ball with its last/first
  participant respectively, which becomes ``MatchState.ball_holder_id``.
* Goals and saves do not emit a possession-change event: a goal hands the
  kickoff to the conceded side, and a save leaves the ball with the goalkeeper.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Sequence

from brafoot.engine.attributes import PlayerPosition
from brafoot.engine.clock import (
    REGULATION_HALF_SECONDS,
    MatchClock,
    MatchPeriod,
    start_second_half,
)
from brafoot.engine.events import MatchEvent, MatchEventType
from brafoot.engine.matches import MatchSide
from brafoot.engine.randomness import DeterministicStream
from brafoot.engine.rulesets import SimulationRuleset, SimulationTuning
from brafoot.engine.sectors import (
    LineupPlayer,
    TeamSectorProfile,
    calculate_team_sector_profile,
)
from brafoot.engine.segments import SegmentStopReason, advance_match_segment
from brafoot.engine.state import KICKOFF_ZONE, MatchState
from brafoot.engine.zones import (
    FieldLane,
    FieldThird,
    FieldZone,
    opposing_perspective,
)

_NEUTRAL = 9 / 19  # rating of an attribute equal to 10
_OPEN_PLAY = "open_play"
_GK = PlayerPosition.GOALKEEPER
_WIDE_ROLES = frozenset(
    {
        PlayerPosition.FULL_BACK,
        PlayerPosition.RIGHT_BACK,
        PlayerPosition.LEFT_BACK,
        PlayerPosition.WINGER,
    }
)
_CENTRAL_ROLES = frozenset(
    {
        PlayerPosition.CENTRE_BACK,
        PlayerPosition.DEFENSIVE_MIDFIELDER,
        PlayerPosition.MIDFIELDER,
        PlayerPosition.STRIKER,
        PlayerPosition.SECOND_STRIKER,
    }
)
_THIRD_WEIGHTS: dict[FieldThird, dict[PlayerPosition, float]] = {
    FieldThird.DEFENSIVE: {
        PlayerPosition.GOALKEEPER: 0.10,
        PlayerPosition.CENTRE_BACK: 1.0,
        PlayerPosition.FULL_BACK: 0.8,
        PlayerPosition.RIGHT_BACK: 0.8,
        PlayerPosition.LEFT_BACK: 0.8,
        PlayerPosition.DEFENSIVE_MIDFIELDER: 0.9,
        PlayerPosition.MIDFIELDER: 0.5,
        PlayerPosition.WINGER: 0.1,
        PlayerPosition.SECOND_STRIKER: 0.1,
        PlayerPosition.STRIKER: 0.05,
    },
    FieldThird.MIDDLE: {
        PlayerPosition.GOALKEEPER: 0.0,
        PlayerPosition.CENTRE_BACK: 0.3,
        PlayerPosition.FULL_BACK: 0.6,
        PlayerPosition.RIGHT_BACK: 0.6,
        PlayerPosition.LEFT_BACK: 0.6,
        PlayerPosition.DEFENSIVE_MIDFIELDER: 1.0,
        PlayerPosition.MIDFIELDER: 1.2,
        PlayerPosition.WINGER: 0.5,
        PlayerPosition.SECOND_STRIKER: 0.6,
        PlayerPosition.STRIKER: 0.3,
    },
    FieldThird.ATTACKING: {
        PlayerPosition.GOALKEEPER: 0.0,
        PlayerPosition.CENTRE_BACK: 0.02,
        PlayerPosition.FULL_BACK: 0.3,
        PlayerPosition.RIGHT_BACK: 0.3,
        PlayerPosition.LEFT_BACK: 0.3,
        PlayerPosition.DEFENSIVE_MIDFIELDER: 0.2,
        PlayerPosition.MIDFIELDER: 0.8,
        PlayerPosition.WINGER: 1.2,
        PlayerPosition.SECOND_STRIKER: 1.2,
        PlayerPosition.STRIKER: 1.3,
    },
}


def _rating(score: float) -> float:
    return (score - 1.0) / 19.0


@dataclass(frozen=True, slots=True)
class TeamRatings:
    """Normalized (0 to 1) team strengths used by the event model."""

    control: float
    progression: float
    pressing: float
    recovery: float
    central_protection: float
    aerial_defense: float
    goalkeeper: float
    aerial_attack: float

    @classmethod
    def from_profile(cls, profile: TeamSectorProfile) -> TeamRatings:
        return cls(
            control=_rating(profile.midfield.control.score),
            progression=_rating(profile.midfield.progression.score),
            pressing=_rating(profile.midfield.pressing.score),
            recovery=_rating(profile.defense.recovery.score),
            central_protection=_rating(profile.defense.central_protection.score),
            aerial_defense=_rating(profile.defense.aerial_defense.score),
            goalkeeper=_rating(profile.defense.goalkeeper.score),
            aerial_attack=_rating(profile.attack.aerial_presence.score),
        )


@dataclass(frozen=True, slots=True)
class SimulatedTeam:
    """One side's eleven assigned players and the ratings derived from them."""

    side: MatchSide
    players: tuple[LineupPlayer, ...]
    goalkeeper_id: int
    ratings: TeamRatings

    def player(self, player_id: int) -> LineupPlayer:
        for player in self.players:
            if player.player_id == player_id:
                return player
        raise ValueError("O jogador não pertence à equipe simulada.")

    @property
    def player_ids(self) -> frozenset[int]:
        return frozenset(player.player_id for player in self.players)


def build_simulated_team(
    side: MatchSide,
    players: Sequence[LineupPlayer],
) -> SimulatedTeam:
    """Validate eleven assigned players and derive the team ratings."""

    if not isinstance(side, MatchSide):
        raise ValueError("O lado da equipe simulada não é válido.")
    players = tuple(players)
    if len(players) != 11:
        raise ValueError("A equipe simulada deve ter exatamente 11 jogadores.")
    goalkeepers = [p for p in players if p.assigned_position is _GK]
    if len(goalkeepers) != 1:
        raise ValueError("A equipe simulada deve ter exatamente um goleiro.")
    profile = calculate_team_sector_profile(players)
    return SimulatedTeam(
        side=side,
        players=players,
        goalkeeper_id=goalkeepers[0].player_id,
        ratings=TeamRatings.from_profile(profile),
    )


@dataclass(frozen=True, slots=True)
class SegmentSimulation:
    """The events and resulting state of one simulated segment."""

    start_state: MatchState
    end_state: MatchState
    events: tuple[MatchEvent, ...]
    stop_reason: SegmentStopReason
    next_sequence: int


@dataclass(frozen=True, slots=True)
class MatchSimulation:
    """A whole regulation match simulated segment by segment."""

    final_state: MatchState
    events: tuple[MatchEvent, ...]
    segments: int

    @property
    def goal_events(self) -> tuple[MatchEvent, ...]:
        return tuple(e for e in self.events if e.event_type is MatchEventType.GOAL)


def simulate_match_segment(
    state: MatchState,
    ruleset: SimulationRuleset,
    home: SimulatedTeam,
    away: SimulatedTeam,
    *,
    next_sequence: int = 1,
) -> SegmentSimulation:
    """Generate the confirmed events of the next segment, then stop at its boundary."""

    if not isinstance(home, SimulatedTeam) or home.side is not MatchSide.HOME:
        raise ValueError("A equipe mandante simulada não é válida.")
    if not isinstance(away, SimulatedTeam) or away.side is not MatchSide.AWAY:
        raise ValueError("A equipe visitante simulada não é válida.")
    if home.player_ids & away.player_ids:
        raise ValueError("Os jogadores das duas equipes devem ser distintos.")
    if not isinstance(next_sequence, int) or isinstance(next_sequence, bool) or next_sequence < 1:
        raise ValueError("A próxima sequência de eventos deve ser um inteiro positivo.")

    segment = advance_match_segment(state, ruleset)  # validates state and ruleset
    play = _Play(
        state=state,
        end_seconds=segment.end_state.clock.elapsed_seconds,
        tuning=ruleset.tuning,
        teams={MatchSide.HOME: home, MatchSide.AWAY: away},
        next_sequence=next_sequence,
    )
    play.run(segment.stop_reason)
    end_state = replace(
        segment.end_state,
        home_score=play.scores[MatchSide.HOME],
        away_score=play.scores[MatchSide.AWAY],
        possession=play.possession,
        ball_zone=play.zone,
        ball_holder_id=play.holder_id,
        random_step=play.stream.step,
    )
    return SegmentSimulation(
        start_state=state,
        end_state=end_state,
        events=tuple(play.events),
        stop_reason=segment.stop_reason,
        next_sequence=play.sequence,
    )


def simulate_match(
    ruleset: SimulationRuleset,
    home: SimulatedTeam,
    away: SimulatedTeam,
    *,
    random_seed: int,
    kickoff_side: MatchSide = MatchSide.HOME,
) -> MatchSimulation:
    """Simulate a regulation match; the second half is kicked off by the other side."""

    state = MatchState.start(
        ruleset=ruleset, kickoff_side=kickoff_side, random_seed=random_seed
    )
    events: list[MatchEvent] = []
    sequence = 1
    segments = 0
    while state.clock.period is not MatchPeriod.FULL_TIME:
        if state.clock.period is MatchPeriod.HALF_TIME:
            state = replace(
                state,
                clock=start_second_half(state.clock),
                possession=_other(kickoff_side),
                ball_zone=KICKOFF_ZONE,
                ball_holder_id=None,
            )
        result = simulate_match_segment(
            state, ruleset, home, away, next_sequence=sequence
        )
        events.extend(result.events)
        state = result.end_state
        sequence = result.next_sequence
        segments += 1
    return MatchSimulation(final_state=state, events=tuple(events), segments=segments)


def _other(side: MatchSide) -> MatchSide:
    return MatchSide.AWAY if side is MatchSide.HOME else MatchSide.HOME


class _Play:
    """Mutable bookkeeping for the segment being generated (never escapes this module)."""

    def __init__(
        self,
        *,
        state: MatchState,
        end_seconds: int,
        tuning: SimulationTuning,
        teams: dict[MatchSide, SimulatedTeam],
        next_sequence: int,
    ) -> None:
        self.period = state.clock.period
        self.t = state.clock.elapsed_seconds
        self.end_seconds = end_seconds
        self.tuning = tuning
        self.teams = teams
        self.sequence = next_sequence
        self.events: list[MatchEvent] = []
        self.stream = DeterministicStream(state.random_seed, state.random_step)
        self.scores = {MatchSide.HOME: state.home_score, MatchSide.AWAY: state.away_score}
        self.possession = state.possession
        self.zone = state.ball_zone
        self.holder_id = state.ball_holder_id
        if self.holder_id is not None and self.holder_id not in teams[self.possession].player_ids:
            raise ValueError("O portador da bola não pertence à equipe com a posse.")

    # ------------------------------------------------------------------ loop
    def run(self, stop_reason: SegmentStopReason) -> None:
        if self.t in (0, REGULATION_HALF_SECONDS) and self.period in (
            MatchPeriod.FIRST_HALF,
            MatchPeriod.SECOND_HALF,
        ):
            label = "primeiro" if self.period is MatchPeriod.FIRST_HALF else "segundo"
            self.emit(
                MatchEventType.PERIOD_START, None, (), None, None, None, None,
                f"Início do {label} tempo.",
            )
        if self.holder_id is None:
            self.holder_id = self._kickoff_taker(self.possession)

        while True:
            attacker = self.teams[self.possession]
            action = self._choose_action(attacker)
            duration = self.stream.between(*self._duration_range(action))
            if self.t + duration >= self.end_seconds:
                break
            self.t += duration
            getattr(self, f"_do_{action}")()

        if stop_reason in (SegmentStopReason.HALF_TIME, SegmentStopReason.FULL_TIME):
            ended = (
                MatchPeriod.HALF_TIME
                if stop_reason is SegmentStopReason.HALF_TIME
                else MatchPeriod.FULL_TIME
            )
            self.t = self.end_seconds
            self.period = ended
            label = "do primeiro tempo" if ended is MatchPeriod.HALF_TIME else "da partida"
            self.emit(
                MatchEventType.PERIOD_END, None, (), None, None, None, None,
                f"Fim {label}.",
            )

    def emit(
        self,
        event_type: MatchEventType,
        side: MatchSide | None,
        participants: tuple[int, ...],
        origin: FieldZone | None,
        destination: FieldZone | None,
        context: str | None,
        outcome: str | None,
        explanation: str,
    ) -> None:
        self.events.append(
            MatchEvent(
                sequence=self.sequence,
                clock=MatchClock(self.t, self.period),
                event_type=event_type,
                team_side=side,
                participant_ids=participants,
                origin_zone=origin,
                destination_zone=destination,
                context=context,
                outcome=outcome,
                explanation=explanation,
            )
        )
        self.sequence += 1

    # --------------------------------------------------------------- helpers
    def _home_bonus(self, side: MatchSide) -> float:
        edge = self.tuning.home_edge
        return edge if side is MatchSide.HOME else -edge

    def _kickoff_taker(self, side: MatchSide) -> int:
        team = self.teams[side]
        return self._pick(team, KICKOFF_ZONE).player_id

    def _pick(
        self,
        team: SimulatedTeam,
        zone: FieldZone,
        *,
        exclude: frozenset[int] = frozenset(),
    ) -> LineupPlayer:
        candidates = [p for p in team.players if p.player_id not in exclude]
        weights = [_zone_weight(p, zone) for p in candidates]
        if sum(weights) <= 0:
            weights = [1.0] * len(candidates)
        return self.stream.choose(candidates, weights)

    def _duration_range(self, action: str) -> tuple[int, int]:
        return {
            "pass": self.tuning.pass_seconds,
            "carry": self.tuning.carry_seconds,
            "cross": self.tuning.cross_seconds,
            "shot": self.tuning.shot_seconds,
        }[action]

    def _choose_action(self, attacker: SimulatedTeam) -> str:
        holder = attacker.player(self.holder_id)
        third, lane = self.zone.third, self.zone.lane
        if third is FieldThird.DEFENSIVE:
            weights = {"pass": 0.80, "carry": 0.20}
        elif third is FieldThird.MIDDLE:
            weights = {"pass": 0.74, "carry": 0.26}
        elif lane is FieldLane.CENTER:
            weights = {"pass": 0.55, "carry": 0.15, "shot": self.tuning.shot_weight_center}
        else:
            weights = {
                "pass": 0.45,
                "carry": 0.15,
                "cross": self.tuning.cross_weight,
                "shot": self.tuning.shot_weight_wide,
            }
        if "shot" in weights:
            weights["shot"] *= 0.3 + 1.4 * _rating(holder.profile.attributes.finalizacao)
        names = list(weights)
        return self.stream.choose(names, [weights[name] for name in names])

    def _lateral_lane(self, lane: FieldLane) -> FieldLane:
        draw = self.stream.random()
        if lane is FieldLane.CENTER:
            return FieldLane.LEFT if draw < 0.5 else FieldLane.RIGHT
        if draw < 0.7:
            return FieldLane.CENTER
        return FieldLane.RIGHT if lane is FieldLane.LEFT else FieldLane.LEFT

    # ---------------------------------------------------------------- actions
    def _do_pass(self) -> None:
        tuning = self.tuning
        attacker = self.teams[self.possession]
        defender = self.teams[_other(self.possession)]
        holder = attacker.player(self.holder_id)
        origin = self.zone

        direction = self.stream.random()
        forward_share = tuning.forward_pass_share + 0.25 * (
            attacker.ratings.progression - defender.ratings.pressing
        )
        if direction < forward_share:
            kind = "forward"
        elif direction < forward_share + tuning.backward_pass_share and (
            origin.third is not FieldThird.DEFENSIVE
        ):
            kind = "backward"
        else:
            kind = "lateral"
        destination = self._pass_destination(origin, kind)
        receiver = self._pick(
            attacker, destination, exclude=frozenset({holder.player_id})
        )

        edge = attacker.ratings.control - defender.ratings.pressing
        edge += self._home_bonus(self.possession)
        skill = _rating(
            0.6 * holder.profile.attributes.passe_curto
            + 0.2 * holder.profile.attributes.visao
            + 0.2 * holder.profile.attributes.decisao
        )
        probability = (
            tuning.pass_base
            + tuning.pass_slope * edge
            + tuning.pass_skill_slope * (skill - _NEUTRAL)
        )
        if kind == "forward":
            probability -= tuning.forward_pass_penalty
        if destination.third is FieldThird.ATTACKING:
            probability -= tuning.attacking_pass_penalty
        probability = min(
            max(probability, tuning.pass_success_min), tuning.pass_success_max
        )

        participants = (holder.player_id, receiver.player_id)
        if self.stream.chance(probability):
            self.emit(
                MatchEventType.PASS, self.possession, participants, origin,
                destination, _OPEN_PLAY, "completed",
                f"Passe de {holder.player_id} para {receiver.player_id}.",
            )
            self.zone = destination
            self.holder_id = receiver.player_id
            return
        self.emit(
            MatchEventType.PASS, self.possession, participants, origin,
            destination, _OPEN_PLAY, "intercepted",
            f"Passe de {holder.player_id} interceptado.",
        )
        self._turnover(destination, "recovered", "intercepta o passe")

    def _pass_destination(self, origin: FieldZone, kind: str) -> FieldZone:
        if kind == "forward":
            third = {
                FieldThird.DEFENSIVE: FieldThird.MIDDLE,
                FieldThird.MIDDLE: FieldThird.ATTACKING,
                FieldThird.ATTACKING: FieldThird.ATTACKING,
            }[origin.third]
            lane = origin.lane
            if origin.third is FieldThird.ATTACKING:
                lane = FieldLane.CENTER if lane is not FieldLane.CENTER else self._lateral_lane(lane)
            elif self.stream.chance(0.35):
                lane = self._lateral_lane(lane)
            return FieldZone(third, lane)
        if kind == "backward":
            third = {
                FieldThird.MIDDLE: FieldThird.DEFENSIVE,
                FieldThird.ATTACKING: FieldThird.MIDDLE,
            }[origin.third]
            return FieldZone(third, origin.lane)
        return FieldZone(origin.third, self._lateral_lane(origin.lane))

    def _do_carry(self) -> None:
        tuning = self.tuning
        attacker = self.teams[self.possession]
        defender = self.teams[_other(self.possession)]
        holder = attacker.player(self.holder_id)
        origin = self.zone

        edge = attacker.ratings.progression - defender.ratings.recovery
        edge += self._home_bonus(self.possession)
        attrs = holder.profile.attributes
        skill = _rating(0.5 * attrs.drible + 0.3 * attrs.controle + 0.2 * attrs.aceleracao)
        probability = min(
            max(
                tuning.carry_base
                + tuning.carry_slope * edge
                + tuning.carry_skill_slope * (skill - _NEUTRAL),
                0.45,
            ),
            0.92,
        )
        if self.stream.chance(tuning.carry_forward_share) and (
            origin.third is not FieldThird.ATTACKING
        ):
            third = (
                FieldThird.MIDDLE
                if origin.third is FieldThird.DEFENSIVE
                else FieldThird.ATTACKING
            )
            destination = FieldZone(third, origin.lane)
        else:
            destination = FieldZone(origin.third, self._lateral_lane(origin.lane))

        if self.stream.chance(probability):
            outcome = "progressed" if destination.third is not origin.third else "kept"
            self.emit(
                MatchEventType.CARRY, self.possession, (holder.player_id,), origin,
                destination, _OPEN_PLAY, outcome,
                f"{holder.player_id} conduz a bola.",
            )
            self.zone = destination
            return
        rival = self._pick(defender, opposing_perspective(origin))
        self.emit(
            MatchEventType.DUEL, self.possession, (holder.player_id, rival.player_id),
            origin, origin, _OPEN_PLAY, "lost",
            f"{holder.player_id} perde a bola para {rival.player_id}.",
        )
        self._take_possession(rival, opposing_perspective(origin), "recovered",
                              f"{rival.player_id} desarma e recupera a bola.")

    def _do_cross(self) -> None:
        tuning = self.tuning
        attacker = self.teams[self.possession]
        defender = self.teams[_other(self.possession)]
        holder = attacker.player(self.holder_id)
        origin = self.zone
        destination = FieldZone(FieldThird.ATTACKING, FieldLane.CENTER)
        receiver = self._pick(
            attacker, destination, exclude=frozenset({holder.player_id})
        )

        edge = attacker.ratings.aerial_attack - defender.ratings.aerial_defense
        edge += self._home_bonus(self.possession)
        attrs = holder.profile.attributes
        skill = _rating(0.7 * attrs.cruzamento + 0.3 * attrs.passe_longo)
        probability = min(
            max(
                tuning.cross_base
                + tuning.cross_slope * edge
                + tuning.cross_skill_slope * (skill - _NEUTRAL),
                0.15,
            ),
            0.75,
        )
        participants = (holder.player_id, receiver.player_id)
        if self.stream.chance(probability):
            self.emit(
                MatchEventType.CROSS, self.possession, participants, origin,
                destination, _OPEN_PLAY, "completed",
                f"Cruzamento de {holder.player_id} para {receiver.player_id}.",
            )
            self.zone = destination
            self.holder_id = receiver.player_id
            if self.stream.chance(tuning.cross_header_share):
                self.t = min(self.t + self.stream.between(2, 4), self.end_seconds - 1)
                self._resolve_shot(receiver, "header")
            return
        self.emit(
            MatchEventType.CROSS, self.possession, participants, origin,
            destination, _OPEN_PLAY, "cleared",
            f"Cruzamento de {holder.player_id} afastado pela defesa.",
        )
        self._turnover(opposing_perspective(origin), "recovered", "afasta o cruzamento")

    def _do_shot(self) -> None:
        self._resolve_shot(self.teams[self.possession].player(self.holder_id), _OPEN_PLAY)

    # ------------------------------------------------------------ shot & goal
    def _resolve_shot(self, shooter: LineupPlayer, context: str) -> None:
        tuning = self.tuning
        attacker_side = self.possession
        attacker = self.teams[attacker_side]
        defender = self.teams[_other(attacker_side)]
        origin = self.zone
        attrs = shooter.profile.attributes
        skill = _rating(
            0.6 * attrs.finalizacao + 0.25 * attrs.potencia_chute + 0.15 * attrs.compostura
        )

        off_target = min(
            max(tuning.shot_off_target - tuning.shot_skill_slope * (skill - _NEUTRAL), 0.15),
            0.6,
        )
        blocked = min(
            max(tuning.shot_blocked + 0.2 * (defender.ratings.central_protection - _NEUTRAL), 0.05),
            0.30,
        )
        draw = self.stream.random()
        if draw < off_target:
            outcome = "off_target"
        elif draw < off_target + blocked:
            outcome = "blocked"
        else:
            outcome = "on_target"
        self.emit(
            MatchEventType.SHOT, attacker_side, (shooter.player_id,), origin, origin,
            context, outcome, f"Finalização de {shooter.player_id}: {outcome}.",
        )

        if outcome == "off_target":
            self._goal_kick(defender)
            return
        if outcome == "blocked":
            rival = self._pick(defender, opposing_perspective(origin))
            self._take_possession(rival, opposing_perspective(origin), "blocked_ball",
                                  f"{rival.player_id} bloqueia a finalização.")
            return

        goalkeeper = defender.player(defender.goalkeeper_id)
        probability = (
            tuning.goal_given_on_target
            + tuning.goal_skill_slope * (skill - defender.ratings.goalkeeper)
        )
        if origin.lane is not FieldLane.CENTER:
            probability *= tuning.wide_shot_goal_factor
        probability = min(max(probability, tuning.goal_min), tuning.goal_max)
        if self.stream.chance(probability):
            self.scores[attacker_side] += 1
            self.emit(
                MatchEventType.GOAL, attacker_side, (shooter.player_id,), origin,
                origin, context, "scored", f"Gol de {shooter.player_id}!",
            )
            self.t += tuning.goal_dead_time_seconds
            self.possession = _other(attacker_side)
            self.zone = KICKOFF_ZONE
            self.holder_id = self._kickoff_taker(self.possession)
            return
        self.emit(
            MatchEventType.SAVE, defender.side, (goalkeeper.player_id,),
            FieldZone(FieldThird.DEFENSIVE, FieldLane.CENTER),
            FieldZone(FieldThird.DEFENSIVE, FieldLane.CENTER),
            context, "saved", f"{goalkeeper.player_id} defende a finalização.",
        )
        self.possession = defender.side
        self.zone = FieldZone(FieldThird.DEFENSIVE, FieldLane.CENTER)
        self.holder_id = goalkeeper.player_id

    def _goal_kick(self, defender: SimulatedTeam) -> None:
        goalkeeper = defender.player(defender.goalkeeper_id)
        zone = FieldZone(FieldThird.DEFENSIVE, FieldLane.CENTER)
        self.possession = defender.side
        self.zone = zone
        self.holder_id = goalkeeper.player_id
        self.emit(
            MatchEventType.POSSESSION_CHANGE, defender.side, (goalkeeper.player_id,),
            zone, zone, _OPEN_PLAY, "goal_kick",
            f"Tiro de meta para {goalkeeper.player_id}.",
        )

    # ------------------------------------------------------------ possession
    def _turnover(self, lost_at: FieldZone, outcome: str, verb: str) -> None:
        """The defending team wins the ball where the attacker lost it."""

        defender = self.teams[_other(self.possession)]
        zone = opposing_perspective(lost_at)
        rival = self._pick(defender, zone)
        self._take_possession(rival, zone, outcome, f"{rival.player_id} {verb}.")

    def _take_possession(
        self,
        player: LineupPlayer,
        zone: FieldZone,
        outcome: str,
        explanation: str,
    ) -> None:
        side = _other(self.possession)
        self.possession = side
        self.zone = zone
        self.holder_id = player.player_id
        self.emit(
            MatchEventType.POSSESSION_CHANGE, side, (player.player_id,), zone, zone,
            _OPEN_PLAY, outcome, explanation,
        )


def _zone_weight(player: LineupPlayer, zone: FieldZone) -> float:
    position = player.assigned_position
    weight = _THIRD_WEIGHTS[zone.third][position]
    if zone.lane is FieldLane.CENTER:
        if position in _CENTRAL_ROLES:
            weight *= 1.4
        elif position in _WIDE_ROLES:
            weight *= 0.6
        return weight
    if position in _WIDE_ROLES:
        weight *= 1.6
    elif position in {
        PlayerPosition.CENTRE_BACK,
        PlayerPosition.STRIKER,
        PlayerPosition.DEFENSIVE_MIDFIELDER,
    }:
        weight *= 0.6
    if zone.lane is FieldLane.LEFT:
        if position is PlayerPosition.LEFT_BACK:
            weight *= 2.0
        elif position is PlayerPosition.RIGHT_BACK:
            weight *= 0.3
    else:
        if position is PlayerPosition.RIGHT_BACK:
            weight *= 2.0
        elif position is PlayerPosition.LEFT_BACK:
            weight *= 0.3
    return weight
