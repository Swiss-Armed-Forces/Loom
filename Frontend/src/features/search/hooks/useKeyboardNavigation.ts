import { useCallback, useEffect, useRef } from "react";
import { flushSync } from "react-dom";

import { useAppDispatch, useAppSelector, useAppStore } from "@app/hooks";
import { selectTopDialog } from "@app/slices/commonSlice";
import {
    fetchNextPage,
    prefetchNextPage,
    queueResultAdvance,
    selectHasMoreResults,
    selectHighlightedFileId,
    selectOrderedFileIds,
    bumpHighlightScroll,
    setHighlightedFileId,
    selectActiveTabFileId,
    selectOpenFileTabs,
    setFileTabDetailTab,
    setActiveTabFileId,
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
    const activeTabFileId = useAppSelector(selectActiveTabFileId);
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
    // on every scroll keypress.
    const scrollableElementRef = useRef<Element | null>(null);
    const scrollablePanelRef = useRef<string | null>(null);

    // Cache the enabled tabs per active panel to avoid a DOM query on every
    // Tab/Shift+Tab keypress.
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
        if (!activeTabFileId) return [];

        // Return cached result if still on the same panel
        if (
            enabledTabsPanelRef.current === activeTabFileId &&
            enabledTabsRef.current !== null
        ) {
            return enabledTabsRef.current;
        }

        // Invalidate cache for the new panel
        enabledTabsPanelRef.current = activeTabFileId;
        enabledTabsRef.current = null;

        const dialog = document.querySelector(
            `[data-file-panel="${activeTabFileId}"]`,
        );
        if (!dialog) return [];

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
    }, [activeTabFileId]);

    const handleTabNavigationDirection = useCallback(
        (direction: "left" | "right") => {
            const enabledTabs = getEnabledTabs();
            if (enabledTabs.length === 0) return;

            // Find current tab's position in enabled tabs
            const activeTab = openFileTabs.find(
                (t) => t.fileId === activeTabFileId,
            );
            const currentIndex = enabledTabs.indexOf(
                activeTab?.detailTab ?? FileDetailTab.Rendered,
            );

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

            if (activeTabFileId) {
                dispatch(
                    setFileTabDetailTab({
                        fileId: activeTabFileId,
                        detailTab: enabledTabs[nextIndex],
                    }),
                );
            }
        },
        [activeTabFileId, openFileTabs, getEnabledTabs, dispatch],
    );

    const handleCenterTabNavigation = useCallback(
        (direction: "left" | "right") => {
            // Build ordered list: [null (Results), ...file tab IDs]
            const tabIds: (string | null)[] = [
                null,
                ...openFileTabs.map((t) => t.fileId),
            ];
            if (tabIds.length <= 1) return; // Only Results tab, nothing to navigate

            const currentIndex = tabIds.indexOf(activeTabFileId);
            let nextIndex: number;
            if (currentIndex === -1) {
                nextIndex = direction === "right" ? 0 : tabIds.length - 1;
            } else if (direction === "right") {
                nextIndex = (currentIndex + 1) % tabIds.length;
            } else {
                nextIndex = (currentIndex - 1 + tabIds.length) % tabIds.length;
            }

            dispatch(setActiveTabFileId(tabIds[nextIndex]));
        },
        [activeTabFileId, openFileTabs, dispatch],
    );

    const handleSummaryTabNavigation = useCallback(
        (direction: "left" | "right") => {
            const card = document.querySelector("[data-highlighted='true']");
            if (!card) return;

            const allTabs = Array.from(card.querySelectorAll("[role='tab']"));
            const enabledTabs = allTabs.filter(
                (tab) =>
                    tab.getAttribute("aria-disabled") !== "true" &&
                    !tab.classList.contains("Mui-disabled"),
            );
            if (enabledTabs.length === 0) return;

            const currentIndex = enabledTabs.findIndex(
                (tab) => tab.getAttribute("aria-selected") === "true",
            );

            let nextIndex: number;
            if (currentIndex === -1) {
                nextIndex = direction === "right" ? 0 : enabledTabs.length - 1;
            } else if (direction === "right") {
                nextIndex = (currentIndex + 1) % enabledTabs.length;
            } else {
                nextIndex =
                    (currentIndex - 1 + enabledTabs.length) %
                    enabledTabs.length;
            }

            (enabledTabs[nextIndex] as HTMLElement).click();
        },
        [],
    );

    const handleDialogScroll = useCallback(
        (direction: "up" | "down", amount?: number) => {
            // Find the scrollable element within the active file panel
            const panel = activeTabFileId
                ? document.querySelector(
                      `[data-file-panel="${activeTabFileId}"]`,
                  )
                : null;
            if (!panel) return;

            // Use cached scrollable element; invalidate when the panel changes
            if (scrollablePanelRef.current !== activeTabFileId) {
                scrollablePanelRef.current = activeTabFileId;
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
        [activeTabFileId],
    );

    // Click a button by aria-label or title within the appropriate container
    const clickActionButton = useCallback(
        (actionKey: string) => {
            const container = activeTabFileId
                ? document.querySelector(
                      `[data-file-panel="${activeTabFileId}"]`,
                  )
                : document.querySelector("[data-highlighted='true']");

            if (!container) return;

            // Find by aria-label first, then fall back to title
            let clickable = container.querySelector(
                `button[aria-label="${actionKey}"], a[aria-label="${actionKey}"]`,
            );

            if (!clickable) {
                clickable = container.querySelector(
                    `button[title="${actionKey}"], a[title="${actionKey}"]`,
                );
            }

            if (clickable && !(clickable as HTMLButtonElement).disabled) {
                (clickable as HTMLElement).click();
            }
        },
        [activeTabFileId],
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
                    // With a file panel open these scroll it; otherwise they
                    // page the result list, which had no keyboard equivalent.
                    case "pageDown":
                        if (activeTabFileId !== null) {
                            handleDialogScroll("down");
                        } else {
                            queueResultMove(resultPageStep());
                        }
                        return;
                    case "pageUp":
                        if (activeTabFileId !== null) {
                            handleDialogScroll("up");
                        } else {
                            queueResultMove(-resultPageStep());
                        }
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
                    case "prevCenterTab":
                        handleCenterTabNavigation("left");
                        break;
                    case "nextCenterTab":
                        handleCenterTabNavigation("right");
                        break;
                    case "openOrClose":
                        if (activeTabFileId !== null) {
                            dispatch(closeFileTabThunk(activeTabFileId));
                        } else if (highlightedFileId !== null) {
                            clickActionButton("preview");
                        }
                        break;
                    case "open":
                        if (
                            activeTabFileId === null &&
                            highlightedFileId !== null
                        ) {
                            clickActionButton("preview");
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
                    case "fullscreen":
                        if (activeTabFileId !== null) {
                            flushSync(() => {
                                dispatch(
                                    setFileTabDetailTab({
                                        fileId: activeTabFileId,
                                        detailTab: FileDetailTab.Rendered,
                                    }),
                                );
                            });
                            const panel = document.querySelector(
                                `[data-file-panel="${activeTabFileId}"]`,
                            );
                            const btn = panel?.querySelector(
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
                    case "flag":
                        clickActionButton("flagged");
                        break;
                    case "seen":
                        clickActionButton("seen");
                        break;
                    case "tag":
                        clickActionButton("tags-input");
                        break;
                    case "navigateParentFile": {
                        const currentFileId =
                            activeTabFileId ?? highlightedFileId;
                        if (!currentFileId) break;
                        const parentId =
                            store.getState().search.files[currentFileId]
                                ?.preview?.parentId;
                        if (!parentId) break;
                        if (
                            activeTabFileId === null &&
                            highlightedFileId !== null
                        ) {
                            dispatch(
                                revealFileThunk({
                                    fileId: parentId,
                                    openInTab: false,
                                }),
                            );
                        } else {
                            dispatch(openFileTabThunk({ fileId: parentId }));
                        }
                        break;
                    }
                    case "NavigateChildFile": {
                        const currentFileId =
                            activeTabFileId ?? highlightedFileId;
                        if (!currentFileId) break;
                        const currentPreview =
                            store.getState().search.files[currentFileId]
                                ?.preview;
                        const attachments = currentPreview?.attachments;
                        if (!attachments?.length) break;
                        if (attachments.length === 1) {
                            if (
                                activeTabFileId === null &&
                                highlightedFileId !== null
                            ) {
                                dispatch(
                                    revealFileThunk({
                                        fileId: attachments[0].id,
                                        openInTab: false,
                                    }),
                                );
                            } else {
                                dispatch(
                                    openFileTabThunk({
                                        fileId: attachments[0].id,
                                    }),
                                );
                            }
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
                    case "escapeAction":
                        document.dispatchEvent(
                            new CustomEvent("loom:close-menus"),
                        );
                        if (activeTabFileId !== null) {
                            dispatch(closeFileTabThunk(activeTabFileId));
                        } else if (highlightedFileId !== null) {
                            dispatch(setHighlightedFileId(null));
                        }
                        break;
                    case "scrollDown":
                        if (activeTabFileId !== null) {
                            handleDialogScroll("down", SCROLL_STEP_PX);
                        }
                        break;
                    case "scrollUp":
                        if (activeTabFileId !== null) {
                            handleDialogScroll("up", SCROLL_STEP_PX);
                        }
                        break;
                    case "closePanel":
                        if (activeTabFileId !== null) {
                            dispatch(closeFileTabThunk(activeTabFileId));
                        }
                        break;
                    case "summaryTabLeft":
                        if (highlightedFileId !== null) {
                            handleSummaryTabNavigation("left");
                        }
                        break;
                    case "summaryTabRight":
                        if (highlightedFileId !== null) {
                            handleSummaryTabNavigation("right");
                        }
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
            handleCenterTabNavigation,
            handleSummaryTabNavigation,
            handleDialogScroll,
            activeTabFileId,
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
