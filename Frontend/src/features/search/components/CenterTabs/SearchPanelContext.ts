import { createContext, RefObject, useContext } from "react";

/**
 * The element the search results scroll inside.
 *
 * The result list is virtualized but does not own its scroller: the panel
 * belongs to `CenterTabs`, which also hangs the scroll-to-top button and the
 * tour anchor off it. Handing the ref down is what lets the virtualizer attach
 * to it instead of a container of its own — and saves the list guessing with
 * `closest("[class*='searchPanel']")`.
 */
export interface SearchPanelContextValue {
    scrollRef: RefObject<HTMLDivElement | null>;
    /**
     * Whether the panel is the visible tab.
     *
     * It stays mounted and is hidden with `display: none`, which gives it no
     * layout box at all — every measurement reads zero until it comes back.
     */
    isActive: boolean;
}

export const SearchPanelContext = createContext<SearchPanelContextValue | null>(
    null,
);

export const useSearchPanel = () => useContext(SearchPanelContext);
