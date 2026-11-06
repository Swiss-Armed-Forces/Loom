/**
 * Which rendered rows lay out as one block, and which stand on their own.
 *
 * The result list draws its rendered rows as a single run of normal flow,
 * placed at the offset of the row it starts with, so that a row which grows
 * pushes the next one down instead of being drawn under it. That placement is
 * only right for a *contiguous* run of rows.
 *
 * The rendered range is not always contiguous: the highlighted card is kept
 * rendered however far the reader has scrolled away from it, because a dozen
 * keyboard shortcuts reach it through the DOM, and the tour's anchor is kept
 * rendered for the same reason. Such a row sits wherever it sits in the list,
 * and a block placed at its offset draws every card in it there too — the
 * reader is then looking at empty space, and the cards appear to shuffle in
 * place as they are swapped through a block that no longer moves with the
 * scroll.
 *
 * Pure, and kept apart from the view, because jsdom has no layout engine and
 * this is the rule rather than the measurement.
 */

/** What the split reads off a row; the virtualizer's items carry more. */
export interface RowIndex {
    index: number;
}

export interface RowWindow<T extends RowIndex> {
    /** The contiguous run holding the viewport, laid out as one block. */
    rows: T[];
    /** Rows from elsewhere in the list, each placed at its own offset. */
    pinned: T[];
}

/**
 * Split the rendered rows around the row the viewport starts at.
 *
 * `items` are the rendered rows in ascending index order, which is the order
 * the range extractor produces them in. `anchorIndex` is the first genuinely
 * visible row — the run containing it is the one the reader is looking at, and
 * everything outside that run is pinned there by something other than the
 * scroll position.
 *
 * With nothing pinned — the ordinary case, and every case before a card has
 * been highlighted — `rows` is `items` itself and `pinned` is empty.
 */
export const splitRowWindow = <T extends RowIndex>(
    items: T[],
    anchorIndex: number | null,
): RowWindow<T> => {
    const whole: RowWindow<T> = { rows: items, pinned: [] };
    if (anchorIndex === null) return whole;
    const anchor = items.findIndex((item) => item.index === anchorIndex);
    // The extractor always renders the visible range, so the anchor is there.
    // Were it not, every row still belongs to one run and splitting on a guess
    // would place the reader's own rows at somebody else's offset.
    if (anchor === -1) return whole;

    let first = anchor;
    while (first > 0 && items[first - 1].index === items[first].index - 1) {
        first -= 1;
    }
    let last = anchor;
    while (
        last < items.length - 1 &&
        items[last + 1].index === items[last].index + 1
    ) {
        last += 1;
    }
    if (first === 0 && last === items.length - 1) return whole;

    return {
        rows: items.slice(first, last + 1),
        pinned: [...items.slice(0, first), ...items.slice(last + 1)],
    };
};
