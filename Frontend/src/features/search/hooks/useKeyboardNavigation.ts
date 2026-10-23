import { useCallback, useEffect, useRef } from "react";
import { flushSync } from "react-dom";

import { useAppDispatch, useAppSelector, useAppStore } from "@app/hooks";
import { selectTopDialog } from "@app/slices/commonSlice";
import {
    FileDetailSelection,
    FOLLOW_TAB,
    fileTab,
    sameSelection,
    selectionKey,
} from "@app/slices/fileDetailSelection";
import {
    fetchNextPage,
    prefetchNextPage,
    queueResultAdvance,
    selectHasMoreResults,
    selectHighlightedFileId,
    selectOrderedFileIds,
    bumpHighlightScroll,
    setHighlightedFileId,
    selectFileDetailFileId,
    selectFileDetailSelection,
    selectRightSidebarOpen,
    selectRightSidebarTab,
    selectOpenFileTabs,
    selectFollowDetailTab,
    setDetailTab,
    focusFollowTab,
    focusFileTab,
    setRightSidebarTab,
    RightSidebarTab,
    closeRightSidebar,
    openFileTabThunk,
    revealFileThunk,
    setPendingFullscreenFileId,
    closeFileTabThunk,
} from "@app/slices/searchSlice";
import { selectReverseBindings } from "@app/slices/searchSlice";
import { FileDetailTab } from "@features/common/utils/enums";

const SCROLL_STEP_PX = 300;

// Start the next page once the highlight comes this close to the end of what is
// loaded, so that arriving at the boundary normally costs nothing.
const PREFETCH_WITHIN_RESULTS = 3;

// Used when the viewport cannot be measured — no cards rendered yet, or no
// scroll container found.
const FALLBACK_RESULT_PAGE_STEP = 5;

// Keys the pane under the focus drives itself. The handler is bound to the
// document, so without this an arrow press inside the folder tree moved the
// tree selection *and* the result highlight. Letter shortcuts still reach the
// result list from anywhere, which is how they are expected to work.
const PANE_NAVIGATION_KEYS = new Set([
    "ArrowUp",
    "ArrowDown",
    "ArrowLeft",
    "ArrowRight",
    "Home",
    "End",
    "PageUp",
    "PageDown",
]);

export const useKeyboardNavigation = () => {
    const dispatch = useAppDispatch();
    const topDialog = useAppSelector(selectTopDialog);
    const selection = useAppSelector(selectFileDetailSelection);
    const followDetailTab = useAppSelector(selectFollowDetailTab);
    /**
     * The file whose detail panel is on screen, or null when there is none.
     *
     * The result list is always on screen and is where the keyboard lives.
     * The detail panel is a side column: keys act on it only where the action
     * is about a *document* rather than about the list, and only when the
     * reader can actually see it.
     */
    const detailFileId = useAppSelector(selectFileDetailFileId);
    const rightSidebarOpen = useAppSelector(selectRightSidebarOpen);
    const rightSidebarTab = useAppSelector(selectRightSidebarTab);
    /** Whether the File Detail pane is the one on screen. */
    const fileDetailShowing =
        rightSidebarOpen && rightSidebarTab === RightSidebarTab.FILE_DETAIL;
    const openFileTabs = useAppSelector(selectOpenFileTabs);
    const highlightedFileId = useAppSelector(selectHighlightedFileId);
    const orderedFileIds = useAppSelector(selectOrderedFileIds);
    const hasMoreResults = useAppSelector(selectHasMoreResults);
    const reverseBindings = useAppSelector(selectReverseBindings);
    // The file cache is only read inside hotkey callbacks. Subscribing to it
    // re-rendered the whole search page on every preview that arrived.
    const store = useAppStore();

    // Keep refs so hotkey callbacks don't need these in their dependency arrays.
    const orderedFileIdsRef = useRef(orderedFileIds);
    useEffect(() => {
        orderedFileIdsRef.current = orderedFileIds;
    }, [orderedFileIds]);
    const highlightedFileIdRef = useRef(highlightedFileId);
    useEffect(() => {
        highlightedFileIdRef.current = highlightedFileId;
    }, [highlightedFileId]);
    const hasMoreResultsRef = useRef(hasMoreResults);
    useEffect(() => {
        hasMoreResultsRef.current = hasMoreResults;
    }, [hasMoreResults]);

    // Derive index from file ID for arithmetic operations.
    const highlightedIndex =
        highlightedFileId !== null
            ? orderedFileIds.indexOf(highlightedFileId)
            : null;

    // Fetch the next page before the user reaches it. The thunk's own condition
    // drops the call when the page is already staged or already in flight, so
    // this can fire on every move without issuing anything.
    useEffect(() => {
        if (!hasMoreResults) return;
        if (highlightedIndex === null || highlightedIndex < 0) return;
        if (
            orderedFileIds.length - highlightedIndex >
            PREFETCH_WITHIN_RESULTS
        ) {
            return;
        }
        dispatch(prefetchNextPage());
    }, [highlightedIndex, orderedFileIds.length, hasMoreResults, dispatch]);

    // Cache the scrollable element per active panel to avoid a full DOM scan
    // on every scroll keypress. Keyed by the file on show and not by the tab:
    // the following tab keeps one key while its file moves with the highlight.
    const scrollableElementRef = useRef<Element | null>(null);
    const scrollablePanelRef = useRef<string | null>(null);

    // Cache the enabled tabs per active panel to avoid a DOM query on every
    // Tab/Shift+Tab keypress. Keyed the same way, and for the same reason -
    // which sub-tabs a panel offers is a property of the document it holds.
    const enabledTabsRef = useRef<FileDetailTab[] | null>(null);
    const enabledTabsPanelRef = useRef<string | null>(null);

    const shouldIgnoreKeyEvent = useCallback(
        (event: KeyboardEvent): boolean => {
            if (topDialog) return true;

            // Ignore if already prevented
            if (event.defaultPrevented) {
                return true;
            }

            // Ignore if focus is in an input field
            const activeElement = document.activeElement;
            if (activeElement) {
                const tagName = activeElement.tagName.toLowerCase();
                if (tagName === "input" || tagName === "textarea") {
                    return true;
                }

                // Check for AceEditor
                if (
                    activeElement.classList.contains("ace_text-input") ||
                    activeElement.closest(".ace_editor")
                ) {
                    return true;
                }

                // Check for contenteditable
                if ((activeElement as HTMLElement).isContentEditable) {
                    return true;
                }

                // Leave the pane that owns the focus to its own navigation.
                if (
                    PANE_NAVIGATION_KEYS.has(event.key) &&
                    activeElement.closest("[data-keynav-ignore]")
                ) {
                    return true;
                }

                // Ignore select events if focus is on an interactive element
                const interactiveTags = ["button", "select", "a"];
                const selectKeys = ["Enter"];
                if (
                    interactiveTags.includes(tagName) &&
                    selectKeys.includes(event.key)
                ) {
                    return true;
                }
            }

            return false;
        },
        [topDialog],
    );

    const highlightResultAt = useCallback(
        (index: number) => {
            const order = orderedFileIdsRef.current;
            if (order.length === 0) return;
            const clamped = Math.min(Math.max(index, 0), order.length - 1);
            const fileId = order[clamped];
            if (!fileId || fileId === highlightedFileIdRef.current) return;
            dispatch(setHighlightedFileId(fileId));
            dispatch(bumpHighlightScroll("smart"));
            document.dispatchEvent(new CustomEvent("loom:close-menus"));
        },
        [dispatch],
    );

    /**
     * Move the highlight by `delta` results.
     *
     * Moves that run past the last loaded card are handed to the pagination
     * queue rather than dropped: the overflow is exactly how many cards the user
     * asked for beyond what is loaded, and `fetchNextPage.fulfilled` spends it
     * on the page it brings back. Pressing five times at the boundary therefore
     * advances five cards, and the request is issued once.
     */
    const applyResultMove = useCallback(
        (delta: number) => {
            const order = orderedFileIdsRef.current;
            const count = order.length;
            if (count === 0 || delta === 0) return;

            const current = highlightedFileIdRef.current;
            const index = current ? order.indexOf(current) : -1;
            if (index === -1) {
                highlightResultAt(delta > 0 ? 0 : count - 1);
                return;
            }

            const target = index + delta;
            if (target > count - 1 && hasMoreResultsRef.current) {
                highlightResultAt(count - 1);
                dispatch(queueResultAdvance(target - (count - 1)));
                dispatch(fetchNextPage());
                return;
            }
            highlightResultAt(target);
        },
        [dispatch, highlightResultAt],
    );

    // Key repeat arrives far faster than the list can usefully re-render, so
    // moves are accumulated and applied once per frame. Holding the key still
    // walks the list; it just stops doing a full render per repeat.
    const pendingMoveRef = useRef(0);
    const moveFrameRef = useRef<number | null>(null);
    const queueResultMove = useCallback(
        (delta: number) => {
            pendingMoveRef.current += delta;
            if (moveFrameRef.current !== null) return;
            moveFrameRef.current = requestAnimationFrame(() => {
                moveFrameRef.current = null;
                const total = pendingMoveRef.current;
                pendingMoveRef.current = 0;
                applyResultMove(total);
            });
        },
        [applyResultMove],
    );
    useEffect(
        () => () => {
            if (moveFrameRef.current !== null) {
                cancelAnimationFrame(moveFrameRef.current);
            }
        },
        [],
    );

    // A "page" is what the user can currently see, so PageDown lands on the
    // card that was just below the fold rather than on a fixed count.
    const resultPageStep = useCallback((): number => {
        const container = document.querySelector("[data-search-panel]");
        const cards = document.querySelectorAll(".resultCardParent");
        if (!container || cards.length === 0) {
            return FALLBACK_RESULT_PAGE_STEP;
        }
        const viewport = container.getBoundingClientRect();
        let visible = 0;
        cards.forEach((card) => {
            const rect = card.getBoundingClientRect();
            if (rect.bottom > viewport.top && rect.top < viewport.bottom) {
                visible += 1;
            }
        });
        return Math.max(1, visible);
    }, []);

    const getEnabledTabs = useCallback((): FileDetailTab[] => {
        if (!detailFileId) return [];
        const panelKey = `${selectionKey(selection)}:${detailFileId}`;

        // Return cached result if still on the same panel
        if (
            enabledTabsPanelRef.current === panelKey &&
            enabledTabsRef.current !== null
        ) {
            return enabledTabsRef.current;
        }

        // Invalidate cache for the new panel
        enabledTabsPanelRef.current = panelKey;
        enabledTabsRef.current = null;

        const dialog = activeDetailPanel();
        // Nothing is cached, and nothing navigated, while the panel still
        // holds the file before this one - the following tab loads on a
        // delay, and which sub-tabs are offered is a property of the document.
        if (
            !dialog ||
            dialog.getAttribute("data-file-panel") !== detailFileId
        ) {
            enabledTabsPanelRef.current = null;
            return [];
        }

        const tabElements = dialog.querySelectorAll("[role='tab']");
        if (tabElements.length === 0) return [];

        const enabledTabs: FileDetailTab[] = [];
        tabElements.forEach((tab) => {
            const isDisabled =
                tab.getAttribute("aria-disabled") === "true" ||
                tab.classList.contains("Mui-disabled");

            if (!isDisabled) {
                const tabValue = tab.getAttribute("data-tab-value");
                if (tabValue !== null) {
                    enabledTabs.push(parseInt(tabValue, 10) as FileDetailTab);
                }
            }
        });

        enabledTabsRef.current = enabledTabs;
        return enabledTabs;
    }, [selection, detailFileId]);

    const handleTabNavigationDirection = useCallback(
        (direction: "left" | "right") => {
            const enabledTabs = getEnabledTabs();
            if (enabledTabs.length === 0) return;

            // Find current tab's position in enabled tabs
            const currentDetailTab =
                selection.kind === "file"
                    ? (openFileTabs.find((t) => t.fileId === selection.fileId)
                          ?.detailTab ?? FileDetailTab.Rendered)
                    : followDetailTab;
            const currentIndex = enabledTabs.indexOf(currentDetailTab);

            let nextIndex: number;
            if (currentIndex === -1) {
                // If current tab not found in enabled, start from first or last
                nextIndex = direction === "right" ? 0 : enabledTabs.length - 1;
            } else if (direction === "right") {
                // Move right
                nextIndex = (currentIndex + 1) % enabledTabs.length;
            } else {
                // Move left
                nextIndex =
                    (currentIndex - 1 + enabledTabs.length) %
                    enabledTabs.length;
            }

            dispatch(
                setDetailTab({
                    target: selection,
                    detailTab: enabledTabs[nextIndex],
                }),
            );
        },
        [selection, followDetailTab, openFileTabs, getEnabledTabs, dispatch],
    );

    const handleFileTabNavigation = useCallback(
        (direction: "left" | "right") => {
            // The strip: the following tab, then the ones they opened.
            const tabs: FileDetailSelection[] = [
                FOLLOW_TAB,
                ...openFileTabs.map((t) => fileTab(t.fileId)),
            ];
            if (tabs.length <= 1) return; // Nothing beside the following tab

            const currentIndex = tabs.findIndex((t) =>
                sameSelection(t, selection),
            );
            let nextIndex: number;
            if (currentIndex === -1) {
                nextIndex = direction === "right" ? 0 : tabs.length - 1;
            } else if (direction === "right") {
                nextIndex = (currentIndex + 1) % tabs.length;
            } else {
                nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
            }

            // Cycling a strip the reader cannot see is cycling nothing.
            dispatch(setRightSidebarTab(RightSidebarTab.FILE_DETAIL));
            const next = tabs[nextIndex];
            dispatch(
                next.kind === "follow"
                    ? focusFollowTab()
                    : focusFileTab(next.fileId),
            );
        },
        [selection, openFileTabs, dispatch],
    );

    /**
     * The detail panel in front, or null when the File Detail sidebar is
     * closed or showing nothing.
     *
     * Never looked up by file id: the following tab and an opened tab may
     * hold the same file, and `querySelector` would silently take whichever
     * came first in the document. `FileDetailView` is the only thing that
     * renders panels and marks exactly one of them active.
     */
    const activeDetailPanel = (): Element | null =>
        document.querySelector('[data-file-panel][data-active="true"]');

    const handleDialogScroll = useCallback(
        (direction: "up" | "down", amount?: number) => {
            // Find the scrollable element within the panel in front
            const panel = activeDetailPanel();
            if (!panel) return;

            // Use cached scrollable element; invalidate when the panel changes
            // or when what was cached has left the document - a panel that
            // re-renders onto another file replaces the node underneath it.
            const panelKey = `${selectionKey(selection)}:${detailFileId}`;
            if (
                scrollablePanelRef.current !== panelKey ||
                scrollableElementRef.current?.isConnected === false
            ) {
                scrollablePanelRef.current = panelKey;
                scrollableElementRef.current = null;
            }

            if (!scrollableElementRef.current) {
                const dialogContent = panel.querySelector(
                    ".file-panel-content",
                );
                if (!dialogContent) return;

                // Find the actual scrollable element - check nested containers
                // first for elements with overflow:auto/scroll and content.
                const findScrollableElement = (
                    container: Element,
                ): Element | null => {
                    const scrollableChildren = Array.from(
                        container.querySelectorAll("*"),
                    );
                    for (const child of scrollableChildren) {
                        const style = window.getComputedStyle(child);
                        const isScrollable =
                            style.overflowY === "auto" ||
                            style.overflowY === "scroll";
                        const hasScrollableContent =
                            child.scrollHeight > child.clientHeight;
                        if (isScrollable && hasScrollableContent) {
                            return child;
                        }
                    }
                    const containerStyle = window.getComputedStyle(container);
                    const containerScrollable =
                        containerStyle.overflowY === "auto" ||
                        containerStyle.overflowY === "scroll";
                    if (
                        containerScrollable &&
                        container.scrollHeight > container.clientHeight
                    ) {
                        return container;
                    }
                    return null;
                };

                scrollableElementRef.current =
                    findScrollableElement(dialogContent);
            }

            const scrollableElement = scrollableElementRef.current;
            if (!scrollableElement) return;

            const scrollAmount =
                amount !== undefined
                    ? amount
                    : Math.max(scrollableElement.clientHeight, SCROLL_STEP_PX);
            const currentScroll = scrollableElement.scrollTop;
            const newScroll =
                direction === "down"
                    ? currentScroll + scrollAmount
                    : currentScroll - scrollAmount;

            scrollableElement.scrollTo({
                top: Math.max(0, newScroll),
                behavior: "smooth",
            });
        },
        [selection, detailFileId],
    );

    const actionButtonIn = (
        container: Element | null,
        actionKey: string,
    ): HTMLElement | null => {
        if (!container) return null;
        // Find by aria-label first, then fall back to title
        const clickable =
            container.querySelector(
                `button[aria-label="${actionKey}"], a[aria-label="${actionKey}"]`,
            ) ??
            container.querySelector(
                `button[title="${actionKey}"], a[title="${actionKey}"]`,
            );
        if (!clickable || (clickable as HTMLButtonElement).disabled) {
            return null;
        }
        return clickable as HTMLElement;
    };

    /**
     * Press a file action by its label, on the document the reader is on.
     *
     * That document is the one the pane is showing, or the highlight when no
     * pane is. Both places it can be pressed are checked against it rather
     * than taken on trust:
     *
     * - the panel in front may hold the file *before* the current one, since
     *   the following tab loads on a delay, and flagging or re-indexing that
     *   one is a write to a document the reader has already left;
     * - the highlighted card is a different document whenever the reader has
     *   selected a file tab, so it is a fallback only while it is the subject.
     *
     * The fallback is reached by more than "no panel": a panel draws a
     * skeleton until its preview lands, and at the widths the sidebar is
     * usually dragged to it keeps tag, share and download in the overflow
     * menu. Where neither place carries the button, nothing is pressed.
     */
    const clickActionButton = useCallback(
        (actionKey: string) => {
            const subject = detailFileId ?? highlightedFileId;
            const panel = activeDetailPanel();
            const panelIsSubject =
                panel?.getAttribute("data-file-panel") === subject;
            const card =
                highlightedFileId === subject
                    ? document.querySelector("[data-highlighted='true']")
                    : null;
            const clickable =
                (panelIsSubject ? actionButtonIn(panel, actionKey) : null) ??
                actionButtonIn(card, actionKey);
            clickable?.click();
        },
        [detailFileId, highlightedFileId],
    );

    const handleKeyDown = useCallback(
        (event: KeyboardEvent) => {
            if (shouldIgnoreKeyEvent(event)) {
                return;
            }

            // Build pressed keys array for reverse lookup. The modifier order
            // has to match the one KeyRecorder stores a binding in, or a combo
            // it recorded never resolves back to its action.
            const pressedKeys = [
                ...(event.ctrlKey ? ["ctrl"] : []),
                ...(event.shiftKey ? ["shift"] : []),
                ...(event.altKey ? ["alt"] : []),
                ...(event.metaKey ? ["meta"] : []),
                event.key,
            ];

            // Check if pressed keys match a custom binding
            const keyString = pressedKeys
                .map((k) => k.toLowerCase())
                .join(" + ");
            const actionId = reverseBindings[keyString];

            // Handle action with switch statement to avoid object allocation on every keydown
            if (actionId) {
                event.preventDefault();
                switch (actionId) {
                    case "moveDown":
                        queueResultMove(1);
                        break;
                    case "moveUp":
                        queueResultMove(-1);
                        break;
                    // The result list is always on screen now, so these
                    // always page it. A document is scrolled with
                    // scrollUp/scrollDown, which is why those are bound.
                    case "pageDown":
                        queueResultMove(resultPageStep());
                        return;
                    case "pageUp":
                        queueResultMove(-resultPageStep());
                        return;
                    case "firstResult":
                        highlightResultAt(0);
                        break;
                    case "lastResult":
                        highlightResultAt(orderedFileIdsRef.current.length - 1);
                        break;
                    case "loadMore":
                        dispatch(fetchNextPage());
                        break;
                    case "prevTab":
                        handleTabNavigationDirection("left");
                        break;
                    case "nextTab":
                        handleTabNavigationDirection("right");
                        break;
                    case "prevFileTab":
                        handleFileTabNavigation("left");
                        break;
                    case "nextFileTab":
                        handleFileTabNavigation("right");
                        break;
                    // Show or hide the details of whatever is highlighted.
                    // It opens no tab: the following tab already shows it.
                    //
                    // Tested on the pane and not on `detailFileId`, which is
                    // also null when the pane is open on nothing - and then
                    // the key would reopen what the reader asked to close.
                    case "openOrClose":
                        dispatch(
                            fileDetailShowing
                                ? closeRightSidebar()
                                : setRightSidebarTab(
                                      RightSidebarTab.FILE_DETAIL,
                                  ),
                        );
                        break;
                    case "open":
                        if (highlightedFileId !== null) {
                            dispatch(
                                openFileTabThunk({
                                    fileId: highlightedFileId,
                                }),
                            );
                        }
                        break;
                    case "openBackground":
                        if (highlightedFileId !== null) {
                            dispatch(
                                openFileTabThunk({
                                    fileId: highlightedFileId,
                                    background: true,
                                }),
                            );
                        }
                        break;
                    case "focusSearch": {
                        const searchInput = document.querySelector(
                            "[data-search-input]",
                        );
                        if (searchInput) {
                            (searchInput as HTMLElement).focus();
                        }
                        break;
                    }
                    case "fullscreen": {
                        // A panel on screen already showing the subject can
                        // go fullscreen where it stands; otherwise open a tab
                        // and let `pendingFullscreenFileId` do it on arrival.
                        // The panel is asked what it holds rather than taken on
                        // trust - the following tab lags the highlight.
                        const panel = activeDetailPanel();
                        if (
                            detailFileId !== null &&
                            detailFileId ===
                                (highlightedFileId ?? detailFileId) &&
                            panel?.getAttribute("data-file-panel") ===
                                detailFileId
                        ) {
                            flushSync(() => {
                                dispatch(
                                    setDetailTab({
                                        target: selection,
                                        detailTab: FileDetailTab.Rendered,
                                    }),
                                );
                            });
                            const btn = activeDetailPanel()?.querySelector(
                                'button[aria-label="fullscreen"]',
                            ) as HTMLElement | null;
                            btn?.click();
                        } else if (highlightedFileId !== null) {
                            dispatch(
                                setPendingFullscreenFileId(highlightedFileId),
                            );
                            dispatch(
                                openFileTabThunk({
                                    fileId: highlightedFileId,
                                    detailTab: FileDetailTab.Rendered,
                                }),
                            );
                        }
                        break;
                    }
                    case "flag":
                        clickActionButton("flagged");
                        break;
                    case "seen":
                        clickActionButton("seen");
                        break;
                    case "tag":
                        clickActionButton("tags-input");
                        break;
                    // Walk the thread by moving the highlight, so the
                    // following tab shows each step without leaving a trail
                    // of tabs behind. The parent *control* still opens one:
                    // a reader pointing at a thing wants it kept.
                    case "navigateParentFile": {
                        const currentFileId = detailFileId ?? highlightedFileId;
                        if (!currentFileId) break;
                        const parentId =
                            store.getState().search.files[currentFileId]
                                ?.preview?.parentId;
                        if (!parentId) break;
                        dispatch(revealFileThunk({ fileId: parentId }));
                        break;
                    }
                    case "NavigateChildFile": {
                        const currentFileId = detailFileId ?? highlightedFileId;
                        if (!currentFileId) break;
                        const currentPreview =
                            store.getState().search.files[currentFileId]
                                ?.preview;
                        const attachments = currentPreview?.attachments;
                        if (!attachments?.length) break;
                        if (attachments.length === 1) {
                            dispatch(
                                revealFileThunk({ fileId: attachments[0].id }),
                            );
                        } else {
                            clickActionButton("show-attachments");
                        }
                        break;
                    }
                    case "copyLink":
                        clickActionButton("share");
                        break;
                    case "translate":
                        clickActionButton("translate");
                        break;
                    case "summarize":
                        clickActionButton("summarize");
                        break;
                    case "reindex":
                        clickActionButton("re-index");
                        break;
                    case "download":
                        clickActionButton("download");
                        break;
                    // Unwind most-local-first: menus, then an opened tab,
                    // then the sidebar, then the highlight. It never closes a
                    // tab the reader cannot see.
                    case "escapeAction":
                        document.dispatchEvent(
                            new CustomEvent("loom:close-menus"),
                        );
                        if (
                            detailFileId !== null &&
                            selection.kind === "file"
                        ) {
                            dispatch(closeFileTabThunk(selection.fileId));
                        } else if (detailFileId !== null) {
                            dispatch(closeRightSidebar());
                        } else if (highlightedFileId !== null) {
                            dispatch(setHighlightedFileId(null));
                        }
                        break;
                    case "scrollDown":
                        handleDialogScroll("down", SCROLL_STEP_PX);
                        break;
                    case "scrollUp":
                        handleDialogScroll("up", SCROLL_STEP_PX);
                        break;
                    default:
                        break;
                }
                return;
            }
        },
        [
            shouldIgnoreKeyEvent,
            reverseBindings,
            queueResultMove,
            highlightResultAt,
            resultPageStep,
            handleTabNavigationDirection,
            handleFileTabNavigation,
            handleDialogScroll,
            detailFileId,
            fileDetailShowing,
            selection,
            highlightedFileId,
            dispatch,
            clickActionButton,
            store,
        ],
    );

    // The handler changes identity on every highlight move. Call it through a
    // ref so the document listener is attached once for the lifetime of the
    // hook instead of being detached and re-added on each change.
    const handleKeyDownRef = useRef(handleKeyDown);
    handleKeyDownRef.current = handleKeyDown;
    useEffect(() => {
        const listener = (event: KeyboardEvent) =>
            handleKeyDownRef.current(event);
        document.addEventListener("keydown", listener);
        return () => {
            document.removeEventListener("keydown", listener);
        };
    }, []);
};
