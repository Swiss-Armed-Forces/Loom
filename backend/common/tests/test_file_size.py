import pytest

from common.utils.file_size import file_size_to_string


@pytest.mark.parametrize(
    "size, rendered",
    [
        # Bytes carry no decimals: "1023.00 B" is a count of indivisible things.
        (0, "0 B"),
        (1023, "1023 B"),
        # The step into the next unit is at 1024, not at 1000.
        (1024, "1.00 KiB"),
        (1024**2, "1.00 MiB"),
        # Past the last unit the loop falls through rather than running out.
        (1024**8, "1.00 YiB"),
        (1024**9, "1024.00 YiB"),
    ],
)
def test_the_unit_chosen_keeps_the_value_above_one(size: int, rendered: str):
    assert file_size_to_string(size) == rendered
