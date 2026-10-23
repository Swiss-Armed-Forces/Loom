import { memo, useMemo, useRef, useState } from "react";

import { useTour } from "@app/tours/useTour";
import { EmptySearchResults, ScrollToTop } from "@features/search/components";

import { DetailedView } from "../Detailed/DetailedView";

import { SearchPanelContext } from "./SearchPanelContext";
import styles from "./SearchResults.module.css";

/**
 * The centre column: the result list, and nothing else.
 *
 * It owns the scroller rather than the virtualized list, because the list is
 * one of two things that can be inside it and both have to scroll as one. The
 * ref travels to the list through `SearchPanelContext`.
 *
 * Documents are drawn in the File Detail sidebar, so this is never hidden and
 * never measures zero.
 *
 * Memoised, and so is the context value: the parent re-renders on every pubsub
 * message, and a context update walks straight through `DetailedView`'s own
 * `memo` to rebuild the whole virtual window.
 */
export const SearchResults = memo(() => {
    const { showQueryOverview } = useTour();
    const scrollRef = useRef<HTMLDivElement>(null);
    const [hasScrollOffset, setHasScrollOffset] = useState(false);
    const panel = useMemo(() => ({ scrollRef }), []);

    return (
        <div
            className={styles.searchPanel}
            data-tour="search-panel"
            data-search-panel
            onScroll={(e) =>
                setHasScrollOffset((e.target as HTMLDivElement).scrollTop > 0)
            }
            ref={scrollRef}
        >
            <SearchPanelContext.Provider value={panel}>
                {showQueryOverview ? (
                    <EmptySearchResults forceQueryOverview />
                ) : (
                    <DetailedView />
                )}
            </SearchPanelContext.Provider>
            <ScrollToTop
                visible={hasScrollOffset}
                onClick={() => scrollRef.current?.scrollTo(0, 0)}
            />
        </div>
    );
});
SearchResults.displayName = "SearchResults";
