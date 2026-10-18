/**
 * `items` with the entry at `from` moved to sit at `to`.
 *
 * The returned array is a new one and always the same length - a reorder is
 * never allowed to drop or duplicate an entry, because the list it reorders
 * is the set of fields the cards are asked for. An index outside the array,
 * or a move onto the position the entry already holds, gives the array back
 * unchanged so callers can dispatch the result unconditionally.
 */
export const moveItem = <T>(items: T[], from: number, to: number): T[] => {
    if (
        from === to ||
        from < 0 ||
        to < 0 ||
        from >= items.length ||
        to >= items.length
    ) {
        return items;
    }
    const next = [...items];
    const [moved] = next.splice(from, 1);
    next.splice(to, 0, moved);
    return next;
};
