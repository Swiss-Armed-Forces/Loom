import { createContext, RefObject, useContext } from "react";

/**
 * The element the search results scroll inside.
 *
 * The result list is virtualized but does not own its scroller: the panel
 * belongs to `SearchResults`, which also hangs the scroll-to-top button and
 * the tour anchor off it. Handing the ref down is what lets the virtualizer
 * attach to it instead of a container of its own — and saves the list guessing
 * with `closest("[class*='searchPanel']")`.
 */
export interface SearchPanelContextValue {
    scrollRef: RefObject<HTMLDivElement | null>;
}

export const SearchPanelContext = createContext<SearchPanelContextValue | null>(
    null,
);

export const useSearchPanel = () => useContext(SearchPanelContext);
