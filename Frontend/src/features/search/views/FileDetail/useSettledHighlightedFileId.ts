import { useEffect, useState } from "react";

import { HIGHLIGHT_SETTLE_MS } from "@app/highlightSettle";
import { useAppStore } from "@app/hooks";
import { selectHighlightedFileId } from "@app/slices/searchSlice";

/**
 * The highlight, once it has stopped moving.
 *
 * The following tab loads a whole file, and a reader walking the list with `j`
 * is not asking for each of the files they pass. Without this, holding the key
 * costs a preview and a document fetch per card.
 *
 * Subscribed to the store rather than read with `useAppSelector`: a selector
 * re-renders on every move, which is the whole sidebar - the strip and a
 * `FileDetailPanel` per open tab, each a MUI `Tabs` that measures itself - per
 * keypress. Debouncing the value alone would save the fetches and none of that.
 */
export const useSettledHighlightedFileId = (): string | null => {
    const store = useAppStore();
    const [settled, setSettled] = useState(() =>
        selectHighlightedFileId(store.getState()),
    );

    useEffect(() => {
        let timer: ReturnType<typeof setTimeout> | undefined;
        // Seeded from the store rather than from `settled`, and applied at
        // once: a highlight that moved between the first render and this
        // subscription is a move nothing else will report.
        let last = selectHighlightedFileId(store.getState());
        setSettled(last);

        const unsubscribe = store.subscribe(() => {
            const current = selectHighlightedFileId(store.getState());
            // Every action reaches this, so the timer restarts only for a move.
            // Restarting it on each unrelated dispatch - a preview landing, say
            // - would hold the following tab back for as long as they keep
            // arriving.
            if (current === last) return;
            last = current;
            clearTimeout(timer);
            timer = setTimeout(() => setSettled(current), HIGHLIGHT_SETTLE_MS);
        });

        return () => {
            clearTimeout(timer);
            unsubscribe();
        };
    }, [store]);

    return settled;
};
