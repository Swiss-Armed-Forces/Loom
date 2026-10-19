"""One spelling of a byte count, for the whole package.

There were four: `report._gib`, `watch.GIBIBYTE`, and two inline `(1024 ** 3)` literals
in `__main__` that used neither. They agreed, which is the only reason nobody noticed --
and "GiB" appears on the console pane, in the journal and in the operator's final
summary line, where three of them being 1.1 and one being 1.2 is the kind of
disagreement that costs an afternoon.

A leaf module with no imports of its own, because the three callers do not import each
other: `watch` reaches only `progress`, `report` only `jsonfile` and `manifest`.
"""

GIBIBYTE = 1024**3


def gib(value: float, width: int = 0) -> str:
    """`value` bytes as gibibytes, to one decimal and with the unit.

    `width` pads the number so a column of them lines up, which is what the pane's per-
    device rows need and what a sentence in the journal does not.
    """
    return f"{value / GIBIBYTE:{width}.1f} GiB"
