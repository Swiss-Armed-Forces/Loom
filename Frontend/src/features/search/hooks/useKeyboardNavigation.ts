import { useCallback, useEffect, useRef } from "react";
import { flushSync } from "react-dom";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import { selectIsLoading, selectTopDialog } from "@app/slices/commonSlice";
import {
    selectHighlightedFileId,
    selectOrderedFileIds,
    selectTotalFiles,
    selectLoadedFiles,
    selectLastFileSortId,
    selectQuery,
    selectFiles,
    bumpHighlightScroll,
    setHighlightedFileId,
    updateQuery,
    selectActiveTabFileId,
    selectOpenFileTabs,
    setFileTabDetailTab,
    setActiveTabFileId,
    openFileTabThunk,
    setPendingFullscreenFileId,
    closeFileTabThunk,
} from "@app/slices/searchSlice";
import { selectReverseBindings } from "@app/slices/searchSlice";
import { FileDetailTab } from "@features/common/utils/enums";

const SCROLL_STEP_PX = 300;

export const useKeyboardNavigation = () => {
    const dispatch = useAppDispatch();
    const topDialog = useAppSelector(selectTopDialog);
    const activeTabFileId = useAppSelector(selectActiveTabFileId);
    const openFileTabs = useAppSelector(selectOpenFileTabs);
    const highlightedFileId = useAppSelector(selectHighlightedFileId);
    const orderedFileIds = useAppSelector(selectOrderedFileIds);
    const totalFiles = useAppSelector(selectTotalFiles);
    const loadedFiles = useAppSelector(selectLoadedFiles);
    const lastFileSortId = useAppSelector(selectLastFileSortId);
    const query = useAppSelector(selectQuery);
    const isLoading = useAppSelector(selectIsLoading);
    const files = useAppSelector(selectFiles);
    const reverseBindings = useAppSelector(selectReverseBindings);

    // Keep refs so hotkey callbacks don't need these in their dependency arrays.
    const filesRef = useRef(files);
    useEffect(() => {
        filesRef.current = files;
    }, [files]);
    const orderedFileIdsRef = useRef(orderedFileIds);
    useEffect(() => {
        orderedFileIdsRef.current = orderedFileIds;
    }, [orderedFileIds]);
    // Derive index from file ID for arithmetic operations.
    const highlightedIndex =
        highlightedFileId !== null
            ? orderedFileIds.indexOf(highlightedFileId)
            : null;

    // Retry pagination once loading clears (handles the case where the user
    // pressed down while a previous request was still in-flight).
    useEffect(() => {
        if (!wantPaginationRef.current || isLoading) return;
        if (totalFiles <= loadedFiles) {
            wantPaginationRef.current = false;
            return;
        }
        wantPaginationRef.current = false;
        pendingAdvanceFromRef.current = loadedFiles;
        dispatch(updateQuery({ id: query?.id, sortId: lastFileSortId }));
    }, [
        isLoading,
        loadedFiles,
        totalFiles,
        query?.id,
        lastFileSortId,
        dispatch,
    ]);

    // Advance the highlight to the first new card once pagination delivers results.
    useEffect(() => {
        if (pendingAdvanceFromRef.current === null) return;
        if (loadedFiles <= pendingAdvanceFromRef.current) return;
        const firstNewIndex = pendingAdvanceFromRef.current;
        pendingAdvanceFromRef.current = null;
        dispatch(
            setHighlightedFileId(
                orderedFileIdsRef.current[firstNewIndex] ?? null,
            ),
        );
        dispatch(bumpHighlightScroll("smart"));
    }, [loadedFiles, dispatch]);

    // Pagination tracking:
    // - wantPaginationRef: user pressed down at the last item while isLoading
    //   was true; retry pagination once loading clears.
    // - pendingAdvanceFromRef: pagination was dispatched from this loadedFiles
    //   count; advance the highlight to the first new item when it arrives.
    const wantPaginationRef = useRef<boolean>(false);
    const pendingAdvanceFromRef = useRef<number | null>(null);

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

            // Ignore if modifiers are pressed
            if (event.ctrlKey || event.metaKey || event.altKey) {
                return true;
            }

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

    const handleResultNavigation = useCallback(
        (direction: "up" | "down") => {
            if (loadedFiles === 0) return;

            let newIndex: number;

            if (highlightedIndex === null) {
                newIndex = direction === "down" ? 0 : loadedFiles - 1;
            } else if (highlightedIndex >= loadedFiles) {
                // On temp card (outside current results) — reset to top
                newIndex = 0;
            } else if (direction === "down") {
                if (highlightedIndex >= loadedFiles - 1) {
                    // At the last item, try to load more
                    if (totalFiles > loadedFiles) {
                        if (!isLoading) {
                            pendingAdvanceFromRef.current = loadedFiles;
                            wantPaginationRef.current = false;
                            dispatch(
                                updateQuery({
                                    id: query?.id,
                                    sortId: lastFileSortId,
                                }),
                            );
                        } else {
                            // Loading is in progress; retry once it clears.
                            wantPaginationRef.current = true;
                        }
                    }
                    return;
                }
                newIndex = highlightedIndex + 1;
            } else {
                newIndex = Math.max(0, highlightedIndex - 1);
            }

            dispatch(
                setHighlightedFileId(
                    orderedFileIdsRef.current[newIndex] ?? null,
                ),
            );
            dispatch(bumpHighlightScroll("smart"));
            document.dispatchEvent(new CustomEvent("loom:close-menus"));
        },
        [
            highlightedIndex,
            totalFiles,
            loadedFiles,
            isLoading,
            query?.id,
            lastFileSortId,
            dispatch,
        ],
    );

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

            // Build pressed keys array for reverse lookup
            const pressedKeys = [
                ...(event.ctrlKey ? ["ctrl"] : []),
                ...(event.shiftKey ? ["shift"] : []),
                ...(event.metaKey ? ["meta"] : []),
                ...(event.altKey ? ["alt"] : []),
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
                        handleResultNavigation("down");
                        break;
                    case "moveUp":
                        handleResultNavigation("up");
                        break;
                    case "pageDown":
                        handleDialogScroll("down");
                        return;
                    case "pageUp":
                        handleDialogScroll("up");
                        return;
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
                            filesRef.current[currentFileId]?.preview?.parentId;
                        if (!parentId) break;
                        dispatch(openFileTabThunk({ fileId: parentId }));
                        break;
                    }
                    case "NavigateChildFile": {
                        const currentFileId =
                            activeTabFileId ?? highlightedFileId;
                        if (!currentFileId) break;
                        const currentPreview =
                            filesRef.current[currentFileId]?.preview;
                        const attachments = currentPreview?.attachments;
                        if (!attachments?.length) break;
                        if (attachments.length === 1) {
                            dispatch(
                                openFileTabThunk({
                                    fileId: attachments[0].id,
                                }),
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
            handleResultNavigation,
            handleTabNavigationDirection,
            handleCenterTabNavigation,
            handleSummaryTabNavigation,
            handleDialogScroll,
            activeTabFileId,
            highlightedFileId,
            dispatch,
            clickActionButton,
        ],
    );

    useEffect(() => {
        document.addEventListener("keydown", handleKeyDown);
        return () => {
            document.removeEventListener("keydown", handleKeyDown);
        };
    }, [handleKeyDown]);
};
