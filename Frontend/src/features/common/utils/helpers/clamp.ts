/**
 * Restricts a value to the inclusive range [min, max].
 *
 * Example: clamp(12, 0, 10) → 10
 */
export const clamp = (value: number, min: number, max: number): number =>
    Math.min(Math.max(value, min), max);
