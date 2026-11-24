"""Pure match commands applied only at confirmed simulation interruptions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import Enum

from brafoot.engine.lineups import (
    AvailabilityStatus,
    Lineup,
    Starter,
    require_valid_lineup,
)
from brafoot.engine.matches import MatchSide
from brafoot.engine.rulesets import SimulationRuleset


class CommandInterruption(str, Enum):
    """A confirmed boundary at which pending commands may affect the future."""

    SEGMENT_BOUNDARY = "segment_boundary"
    HALF_TIME = "half_time"


@dataclass(frozen=True, slots=True)
class AssignedPlayer:
    """A squad player and the role currently assigned on the field."""

    player: Starter
    assigned_position: str

    def __post_init__(self) -> None:
        if not isinstance(self.player, Starter):
            raise ValueError("O jogador atribuído não é válido.")
        if not _is_canonical_code(self.assigned_position):
            raise ValueError("A posição atribuída não é válida.")

    @property
    def player_id(self) -> int:
        return self.player.player_id


@dataclass(frozen=True, slots=True)
class MatchTeamSelection:
    """The immutable active selection used by future match segments."""

    side: MatchSide
    club_id: int
    formation: str
    on_field: tuple[AssignedPlayer, ...]
    bench: tuple[Starter, ...]
    designated_goalkeeper_id: int
    substitutions_used: int = 0
    substitution_windows_used: int = 0
    substituted_out_player_ids: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.side, MatchSide):
            raise ValueError("O lado da seleção não é válido.")
        if not _is_positive_int(self.club_id):
            raise ValueError("O clube da seleção não é válido.")
        if not _is_canonical_code(self.formation):
            raise ValueError("A formação da seleção não é válida.")
        if not isinstance(self.on_field, tuple) or len(self.on_field) != 11:
            raise ValueError("A seleção deve conter exatamente 11 jogadores em campo.")
        if not all(isinstance(player, AssignedPlayer) for player in self.on_field):
            raise ValueError("Os jogadores em campo não são válidos.")
        if not isinstance(self.bench, tuple) or not all(
            isinstance(player, Starter) for player in self.bench
        ):
            raise ValueError("O banco da seleção não é válido.")

        on_field_ids = self.player_ids
        bench_ids = tuple(player.player_id for player in self.bench)
        all_players = tuple(player.player for player in self.on_field) + self.bench
        if (
            len(set(on_field_ids)) != len(on_field_ids)
            or len(set(bench_ids)) != len(bench_ids)
            or set(on_field_ids) & set(bench_ids)
        ):
            raise ValueError("Os jogadores da seleção devem ser distintos.")
        if any(player.club_id != self.club_id for player in all_players):
            raise ValueError("Todos os jogadores da seleção devem pertencer ao clube.")
        if self.designated_goalkeeper_id not in on_field_ids:
            raise ValueError("O goleiro designado deve estar em campo.")
        require_valid_lineup(
            Lineup(
                club_id=self.club_id,
                formation=self.formation,
                starters=tuple(player.player for player in self.on_field),
                designated_goalkeeper_id=self.designated_goalkeeper_id,
                eligible_squad_goalkeeper_ids=tuple(
                    player.player_id
                    for player in all_players
                    if player.position.strip().upper() == "GOL"
                    and player.availability is AvailabilityStatus.AVAILABLE
                ),
            )
        )
        assigned_goalkeeper_ids = tuple(
            player.player_id
            for player in self.on_field
            if player.assigned_position.upper() == "GOL"
        )
        if assigned_goalkeeper_ids != (self.designated_goalkeeper_id,):
            raise ValueError("A seleção deve ter exatamente um goleiro designado.")
        if not _is_non_negative_int(self.substitutions_used):
            raise ValueError("A quantidade de substituições usadas não é válida.")
        if not _is_non_negative_int(self.substitution_windows_used):
            raise ValueError("A quantidade de janelas usadas não é válida.")
        if not _is_unique_positive_int_tuple(self.substituted_out_player_ids):
            raise ValueError("O histórico de jogadores substituídos não é válido.")
        if set(self.substituted_out_player_ids) & (set(on_field_ids) | set(bench_ids)):
            raise ValueError("Um jogador substituído não pode permanecer elegível.")

    @property
    def player_ids(self) -> tuple[int, ...]:
        return tuple(player.player_id for player in self.on_field)

    @classmethod
    def from_lineup(
        cls,
        *,
        side: MatchSide,
        lineup: Lineup,
        bench: tuple[Starter, ...],
    ) -> MatchTeamSelection:
        """Create an active selection from a validated lineup and local bench."""

        if not isinstance(lineup, Lineup):
            raise ValueError("A escalação não é válida.")
        require_valid_lineup(lineup)
        designated_goalkeeper_id = lineup.designated_goalkeeper_id
        if designated_goalkeeper_id is None:
            designated_goalkeeper_id = next(
                player.player_id
                for player in lineup.starters
                if player.position.strip().upper() == "GOL"
            )
        return cls(
            side=side,
            club_id=lineup.club_id,
            formation=lineup.formation,
            on_field=tuple(
                AssignedPlayer(
                    player,
                    "GOL" if player.player_id == designated_goalkeeper_id else _line_role(player),
                )
                for player in lineup.starters
            ),
            bench=bench,
            designated_goalkeeper_id=designated_goalkeeper_id,
        )

    def to_snapshot(self) -> dict[str, object]:
        """Return an explicit persistence representation of the selection."""

        return {
            "side": self.side.value,
            "club_id": self.club_id,
            "formation": self.formation,
            "on_field": [
                {
                    "player": _starter_to_snapshot(assigned.player),
                    "assigned_position": assigned.assigned_position,
                }
                for assigned in self.on_field
            ],
            "bench": [_starter_to_snapshot(player) for player in self.bench],
            "designated_goalkeeper_id": self.designated_goalkeeper_id,
            "substitutions_used": self.substitutions_used,
            "substitution_windows_used": self.substitution_windows_used,
            "substituted_out_player_ids": list(self.substituted_out_player_ids),
        }

    @classmethod
    def from_snapshot(cls, snapshot: Mapping[str, object]) -> MatchTeamSelection:
        """Restore and validate an active selection snapshot."""

        if not isinstance(snapshot, Mapping):
            raise ValueError("O snapshot da seleção não é válido.")
        try:
            on_field = snapshot["on_field"]
            bench = snapshot["bench"]
            substituted_out = snapshot["substituted_out_player_ids"]
            if not _is_snapshot_sequence(on_field) or not _is_snapshot_sequence(bench):
                raise ValueError
            if not _is_snapshot_sequence(substituted_out):
                raise ValueError
            return cls(
                side=MatchSide(snapshot["side"]),
                club_id=snapshot["club_id"],
                formation=snapshot["formation"],
                on_field=tuple(_assigned_player_from_snapshot(item) for item in on_field),
                bench=tuple(_starter_from_snapshot(item) for item in bench),
                designated_goalkeeper_id=snapshot["designated_goalkeeper_id"],
                substitutions_used=snapshot["substitutions_used"],
                substitution_windows_used=snapshot["substitution_windows_used"],
                substituted_out_player_ids=tuple(substituted_out),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("O snapshot da seleção não é válido.") from error


@dataclass(frozen=True, slots=True)
class Substitution:
    """One player replacement inside a substitution command."""

    player_out_id: int
    player_in_id: int
    assigned_position: str

    def __post_init__(self) -> None:
        if not _is_positive_int(self.player_out_id) or not _is_positive_int(
            self.player_in_id
        ):
            raise ValueError("Os jogadores da substituição não são válidos.")
        if self.player_out_id == self.player_in_id:
            raise ValueError("Os jogadores da substituição devem ser diferentes.")
        if not _is_canonical_code(self.assigned_position):
            raise ValueError("A posição atribuída na substituição não é válida.")


@dataclass(frozen=True, slots=True)
class SubstitutionCommand:
    """A persistable batch of replacements requested for one match side."""

    sequence: int
    side: MatchSide
    substitutions: tuple[Substitution, ...]

    def __post_init__(self) -> None:
        if not _is_positive_int(self.sequence):
            raise ValueError("A sequência do comando deve ser um inteiro positivo.")
        if not isinstance(self.side, MatchSide):
            raise ValueError("O lado do comando não é válido.")
        if (
            not isinstance(self.substitutions, tuple)
            or not self.substitutions
            or not all(
                isinstance(substitution, Substitution)
                for substitution in self.substitutions
            )
        ):
            raise ValueError("O comando deve conter substituições válidas.")
        outgoing_ids = tuple(item.player_out_id for item in self.substitutions)
        incoming_ids = tuple(item.player_in_id for item in self.substitutions)
        if (
            len(set(outgoing_ids)) != len(outgoing_ids)
            or len(set(incoming_ids)) != len(incoming_ids)
            or set(outgoing_ids) & set(incoming_ids)
        ):
            raise ValueError("Os jogadores do comando de substituição devem ser únicos.")

    def to_snapshot(self) -> dict[str, object]:
        """Return an explicit persistence representation of the command."""

        return {
            "sequence": self.sequence,
            "side": self.side.value,
            "substitutions": [
                {
                    "player_out_id": substitution.player_out_id,
                    "player_in_id": substitution.player_in_id,
                    "assigned_position": substitution.assigned_position,
                }
                for substitution in self.substitutions
            ],
        }

    @classmethod
    def from_snapshot(cls, snapshot: Mapping[str, object]) -> SubstitutionCommand:
        """Restore and validate a substitution command snapshot."""

        if not isinstance(snapshot, Mapping):
            raise ValueError("O snapshot do comando não é válido.")
        try:
            substitutions = snapshot["substitutions"]
            if not _is_snapshot_sequence(substitutions):
                raise ValueError
            return cls(
                sequence=snapshot["sequence"],
                side=MatchSide(snapshot["side"]),
                substitutions=tuple(
                    _substitution_from_snapshot(item) for item in substitutions
                ),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("O snapshot do comando não é válido.") from error


@dataclass(frozen=True, slots=True)
class CommandViolation:
    """A stable reason why a pending command cannot be accepted."""

    code: str
    message: str
    player_ids: tuple[int, ...] = ()


class CommandValidationError(ValueError):
    """Raised with every violation found while accepting a match command."""

    def __init__(self, violations: tuple[CommandViolation, ...]) -> None:
        self.violations = violations
        super().__init__("; ".join(violation.message for violation in violations))


@dataclass(frozen=True, slots=True)
class SubstitutionApplication:
    """The accepted command and the new selection for subsequent segments."""

    command: SubstitutionCommand
    interruption: CommandInterruption
    previous_selection: MatchTeamSelection
    selection: MatchTeamSelection


def apply_substitution_command(
    selection: MatchTeamSelection,
    command: SubstitutionCommand,
    ruleset: SimulationRuleset,
    interruption: CommandInterruption | None,
) -> SubstitutionApplication:
    """Validate and apply a pending substitution at a confirmed boundary."""

    if not isinstance(selection, MatchTeamSelection):
        raise ValueError("A seleção da partida não é válida.")
    if not isinstance(command, SubstitutionCommand):
        raise ValueError("O comando de substituição não é válido.")
    if not isinstance(ruleset, SimulationRuleset):
        raise ValueError("O conjunto de regras não é válido.")

    violations = _validate_application(selection, command, ruleset, interruption)
    if violations:
        raise CommandValidationError(violations)
    assert interruption is not None

    substitutions_by_outgoing_id = {
        substitution.player_out_id: substitution
        for substitution in command.substitutions
    }
    bench_by_id = {player.player_id: player for player in selection.bench}
    next_on_field = tuple(
        AssignedPlayer(
            bench_by_id[substitution.player_in_id],
            substitution.assigned_position,
        )
        if (substitution := substitutions_by_outgoing_id.get(player.player_id))
        else player
        for player in selection.on_field
    )
    incoming_ids = {
        substitution.player_in_id for substitution in command.substitutions
    }
    outgoing_ids = tuple(
        substitution.player_out_id for substitution in command.substitutions
    )
    designated_goalkeeper_id = selection.designated_goalkeeper_id
    if designated_goalkeeper_id in substitutions_by_outgoing_id:
        designated_goalkeeper_id = next(
            substitution.player_in_id
            for substitution in command.substitutions
            if substitution.assigned_position.upper() == "GOL"
        )
    consumes_window = (
        interruption is not CommandInterruption.HALF_TIME
        or ruleset.half_time_substitution_consumes_window
    )
    next_selection = replace(
        selection,
        on_field=next_on_field,
        bench=tuple(
            player for player in selection.bench if player.player_id not in incoming_ids
        ),
        designated_goalkeeper_id=designated_goalkeeper_id,
        substitutions_used=selection.substitutions_used + len(command.substitutions),
        substitution_windows_used=(
            selection.substitution_windows_used + int(consumes_window)
        ),
        substituted_out_player_ids=(
            selection.substituted_out_player_ids + outgoing_ids
        ),
    )
    return SubstitutionApplication(
        command=command,
        interruption=interruption,
        previous_selection=selection,
        selection=next_selection,
    )


def _validate_application(
    selection: MatchTeamSelection,
    command: SubstitutionCommand,
    ruleset: SimulationRuleset,
    interruption: CommandInterruption | None,
) -> tuple[CommandViolation, ...]:
    violations: list[CommandViolation] = []
    if not isinstance(interruption, CommandInterruption):
        violations.append(
            CommandViolation(
                code="invalid_interruption",
                message="O comando só pode ser aplicado em uma interrupção confirmada.",
            )
        )
    if command.side is not selection.side:
        violations.append(
            CommandViolation(
                code="command_side_mismatch",
                message="O comando pertence ao outro lado da partida.",
            )
        )
    if (
        selection.substitutions_used + len(command.substitutions)
        > ruleset.max_substitutions
    ):
        violations.append(
            CommandViolation(
                code="substitution_limit_exceeded",
                message="O comando excede o limite de substituições.",
            )
        )
    consumes_window = (
        isinstance(interruption, CommandInterruption)
        and (
            interruption is not CommandInterruption.HALF_TIME
            or ruleset.half_time_substitution_consumes_window
        )
    )
    if (
        consumes_window
        and selection.substitution_windows_used + 1
        > ruleset.max_substitution_windows
    ):
        violations.append(
            CommandViolation(
                code="substitution_window_limit_exceeded",
                message="O comando excede o limite de janelas de substituição.",
            )
        )

    on_field_ids = set(selection.player_ids)
    bench_by_id = {player.player_id: player for player in selection.bench}
    missing_outgoing = tuple(
        substitution.player_out_id
        for substitution in command.substitutions
        if substitution.player_out_id not in on_field_ids
    )
    missing_incoming = tuple(
        substitution.player_in_id
        for substitution in command.substitutions
        if substitution.player_in_id not in bench_by_id
    )
    unavailable_incoming = tuple(
        substitution.player_in_id
        for substitution in command.substitutions
        if substitution.player_in_id in bench_by_id
        and bench_by_id[substitution.player_in_id].availability
        is not AvailabilityStatus.AVAILABLE
    )
    if missing_outgoing:
        violations.append(
            CommandViolation(
                code="player_not_on_field",
                message="Todo jogador que sai deve estar em campo.",
                player_ids=missing_outgoing,
            )
        )
    if missing_incoming:
        violations.append(
            CommandViolation(
                code="player_not_on_bench",
                message="Todo jogador que entra deve estar no banco.",
                player_ids=missing_incoming,
            )
        )
    if unavailable_incoming:
        violations.append(
            CommandViolation(
                code="player_not_available",
                message="Jogadores indisponíveis não podem entrar na partida.",
                player_ids=unavailable_incoming,
            )
        )

    goalkeeper_leaves = any(
        substitution.player_out_id == selection.designated_goalkeeper_id
        for substitution in command.substitutions
    )
    incoming_goalkeepers = tuple(
        substitution.player_in_id
        for substitution in command.substitutions
        if substitution.assigned_position.upper() == "GOL"
    )
    if (goalkeeper_leaves and len(incoming_goalkeepers) != 1) or (
        not goalkeeper_leaves and incoming_goalkeepers
    ):
        violations.append(
            CommandViolation(
                code="goalkeeper_replacement_required",
                message="A seleção deve preservar exatamente um jogador designado para o gol.",
                player_ids=incoming_goalkeepers,
            )
        )
    return tuple(violations)


def _line_role(player: Starter) -> str:
    return "LINHA" if player.position.strip().upper() == "GOL" else player.position


def _starter_to_snapshot(player: Starter) -> dict[str, object]:
    return {
        "player_id": player.player_id,
        "club_id": player.club_id,
        "position": player.position,
        "availability": player.availability.value,
    }


def _starter_from_snapshot(snapshot: object) -> Starter:
    if not isinstance(snapshot, Mapping):
        raise ValueError
    return Starter(
        player_id=snapshot["player_id"],
        club_id=snapshot["club_id"],
        position=snapshot["position"],
        availability=AvailabilityStatus(snapshot["availability"]),
    )


def _assigned_player_from_snapshot(snapshot: object) -> AssignedPlayer:
    if not isinstance(snapshot, Mapping):
        raise ValueError
    return AssignedPlayer(
        player=_starter_from_snapshot(snapshot["player"]),
        assigned_position=snapshot["assigned_position"],
    )


def _substitution_from_snapshot(snapshot: object) -> Substitution:
    if not isinstance(snapshot, Mapping):
        raise ValueError
    return Substitution(
        player_out_id=snapshot["player_out_id"],
        player_in_id=snapshot["player_in_id"],
        assigned_position=snapshot["assigned_position"],
    )


def _is_snapshot_sequence(value: object) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes))


def _is_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_unique_positive_int_tuple(value: object) -> bool:
    return (
        isinstance(value, tuple)
        and all(_is_positive_int(item) for item in value)
        and len(set(value)) == len(value)
    )


def _is_canonical_code(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value.strip() == value
