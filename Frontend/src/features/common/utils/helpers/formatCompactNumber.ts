const SI_UNITS: ReadonlyArray<readonly [number, string]> = [
    [1e3, "k"],
    [1e6, "M"],
    [1e9, "G"],
    [1e12, "T"],
    [1e15, "P"],
    [1e18, "E"],
] as const;

/**
 * Formats a number using SI unit prefixes for compact display.
 * Values below 1000 are shown as-is. Above that, the largest applicable
 * SI unit is used with one decimal place (trailing ".0" stripped), switching
 * to no decimal once the value reaches 10 of that unit.
 *
 * Examples: 999 → "999", 1200 → "1.2k", 10000 → "10k", 1500000 → "1.5M"
 */
export const formatCompactNumber = (n: number): string => {
    // Pick the largest SI unit whose threshold is <= n (with a small rounding
    // buffer of 0.9995× so that e.g. 999 500 rounds up to "1M" rather than
    // displaying as "1000k").
    let selectedUnit: readonly [number, string] | undefined;
    for (const unit of SI_UNITS) {
        if (n >= unit[0] * 0.9995) {
            selectedUnit = unit;
        }
    }

    if (!selectedUnit) return String(n);

    const value = n / selectedUnit[0];
    const suffix = selectedUnit[1];
    const formatted =
        value < 10
            ? value.toFixed(1).replace(/\.0$/, "")
            : String(Math.round(value));
    return `${formatted}${suffix}`;
};
