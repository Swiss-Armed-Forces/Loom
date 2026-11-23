def file_size_to_string(size: int) -> str:
    """Render a byte count in the largest IEC unit that keeps it above one."""
    # Powers of 1024, labelled with the IEC units.
    units = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB")
    value = float(size)

    for unit in units[:-1]:
        if value < 1024:
            return f"{value:.2f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024

    return f"{value:.2f} {units[-1]}"
