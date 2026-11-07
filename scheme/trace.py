"""Structured, UI-independent trace records for MAYO scheme operations."""

from dataclasses import dataclass, field
from typing import TypeAlias

TraceData: TypeAlias = dict[
    str,
    str | int | bool | list[int] | list[list[int]] | None,
]
Dimensions: TypeAlias = dict[str, tuple[int, ...]]


@dataclass(frozen=True)
class TraceStep:
    """One pedagogical step recorded during a cryptographic operation.

    Attributes:
        number: One-based position in the containing trace.
        name: Stable machine-readable step identifier.
        description: Short explanation intended for display to a learner.
        data: Small, non-sensitive values associated with the step.
        dimensions: Names and shapes of relevant matrices or vectors.
        status: Outcome such as ``completed``, ``inconsistent``, or ``solved``.
    """

    number: int
    name: str
    description: str
    data: TraceData = field(default_factory=dict)
    dimensions: Dimensions = field(default_factory=dict)
    status: str = "completed"


@dataclass
class SignTrace:
    """Ordered trace of a single MAYO signature-generation operation."""

    steps: list[TraceStep] = field(default_factory=list)

    def add_step(
        self,
        name: str,
        description: str,
        *,
        data: TraceData | None = None,
        dimensions: Dimensions | None = None,
        status: str = "completed",
    ) -> TraceStep:
        """Append a step and assign its one-based sequence number."""
        step = TraceStep(
            number=len(self.steps) + 1,
            name=name,
            description=description,
            data={} if data is None else data,
            dimensions={} if dimensions is None else dimensions,
            status=status,
        )
        self.steps.append(step)
        return step


class SignTraceError(RuntimeError):
    """Signing failure that preserves the trace when tracing was requested."""

    def __init__(self, message: str, trace: SignTrace) -> None:
        super().__init__(message)
        self.trace = trace
