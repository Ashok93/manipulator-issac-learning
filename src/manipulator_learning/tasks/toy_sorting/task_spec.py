"""Task specification for toy sorting by color."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToySortingTaskSpec:
    """High-level task spec used for prompts and color assignment."""

    toy_names: tuple[str, ...] = ("toy_a", "toy_b", "toy_c")
    bin_names: tuple[str, ...] = ("bin_red", "bin_green", "bin_blue")
    colors: tuple[str, ...] = ("red", "green", "blue")
    instruction_template: str = "Sort the {color} toys into the {color} bin."

    def instruction(self, color: str) -> str:
        return self.instruction_template.format(color=color)
