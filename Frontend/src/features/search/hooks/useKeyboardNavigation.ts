import { useCallback, useEffect } from "react";
import { useAppDispatch, useAppSelector } from "../../../app/hooks";
import {
    selectFileDetailData,
    selectHighlightedIndex,
    selectTotalFiles,
    selectLoadedFiles,
    selectLastFileSortId,
    selectQuery,
    setHighlightedIndex,
    setFileDetailData,
    updateQuery,
} from "../searchSlice";
import { selectIsLoading } from "../../common/commonSlice";
import { FileDetailTab } from "../model";

export function useKeyboardNavigation() {
    const dispatch = useAppDispatch();
    const fileDetailData = useAppSelector(selectFileDetailData);
    const highlightedIndex = useAppSelector(selectHighlightedIndex);
    const totalFiles = useAppSelector(selectTotalFiles);
    const loadedFiles = useAppSelector(selectLoadedFiles);
    const lastFileSortId = useAppSelector(selectLastFileSortId);
    const query = useAppSelector(selectQuery);
    const isLoading = useAppSelector(selectIsLoading);

    const isDialogOpen = !!(
        fileDetailData.filePreview && fileDetailData.searchQuery
    );

    const currentTab = fileDetailData.tab ?? FileDetailTab.Rendered;

    const shouldIgnoreKeyEvent = useCallback(
        (event: KeyboardEvent): boolean => {
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

                // Ignore if focus is on an interactive element within a dialog
                // (e.g., buttons, selects) - this prevents keyboard shortcuts
                // from firing when interacting with dialog controls
                const dialog = document.querySelector("[role='dialog']");
                if (dialog && dialog.contains(activeElement)) {
                    const interactiveTags = ["button", "select", "a"];
                    if (interactiveTags.includes(tagName)) {
                        return true;
                    }
                }
            }

            return false;
        },
        [],
    );

    const handleResultNavigation = useCallback(
        (direction: "up" | "down") => {
            if (loadedFiles === 0) return;

            let newIndex: number;

            if (highlightedIndex === null) {
                newIndex = direction === "down" ? 0 : loadedFiles - 1;
            } else if (direction === "down") {
                if (highlightedIndex >= loadedFiles - 1) {
                    // At the last item, try to load more
                    if (totalFiles > loadedFiles && !isLoading) {
                        dispatch(
                            updateQuery({
                                id: query?.id,
                                sortId: lastFileSortId,
                            }),
                        );
                        // Optimistically advance to next item (will be valid when results arrive)
                        dispatch(setHighlightedIndex(highlightedIndex + 1));
                    }
                    return;
                }
                newIndex = highlightedIndex + 1;
            } else {
                newIndex = Math.max(0, highlightedIndex - 1);
            }

            dispatch(setHighlightedIndex(newIndex));
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
        const dialog = document.querySelector("[role='dialog']");
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

        return enabledTabs;
    }, []);

    const handleTabNavigation = useCallback(() => {
        // Round robin through enabled tabs, skipping disabled ones
        const enabledTabs = getEnabledTabs();
        if (enabledTabs.length === 0) return;

        // Find current tab's position in enabled tabs
        const currentIndex = enabledTabs.indexOf(currentTab);

        // Move to next enabled tab, wrap around to first if at end
        let nextIndex: number;
        if (currentIndex === -1) {
            nextIndex = 0;
        } else {
            nextIndex = (currentIndex + 1) % enabledTabs.length;
        }

        dispatch(setFileDetailData({ tab: enabledTabs[nextIndex] }));
    }, [currentTab, getEnabledTabs, dispatch]);

    const handleTabNavigationDirection = useCallback(
        (direction: "left" | "right") => {
            const enabledTabs = getEnabledTabs();
            if (enabledTabs.length === 0) return;

            // Find current tab's position in enabled tabs
            const currentIndex = enabledTabs.indexOf(currentTab);

            let nextIndex: number;
            if (currentIndex === -1) {
                // If current tab not found in enabled, start from first or last
                nextIndex = direction === "right" ? 0 : enabledTabs.length - 1;
            } else if (direction === "right") {
                // Move right, stop at end (no wrap)
                nextIndex = Math.min(enabledTabs.length - 1, currentIndex + 1);
            } else {
                // Move left, stop at beginning (no wrap)
                nextIndex = Math.max(0, currentIndex - 1);
            }

            dispatch(setFileDetailData({ tab: enabledTabs[nextIndex] }));
        },
        [currentTab, getEnabledTabs, dispatch],
    );

    const handleDialogScroll = useCallback((direction: "up" | "down") => {
        // Find the scrollable element within the dialog
        // Could be DialogContent itself, or a nested scroll container (e.g., in FileRenderer)
        const dialog = document.querySelector("[role='dialog']");
        if (!dialog) return;

        // Find all potentially scrollable elements within the dialog content
        const dialogContent = dialog.querySelector(".MuiDialogContent-root");
        if (!dialogContent) return;

        // Find the actual scrollable element - check nested containers first
        // Look for elements with overflow:auto or overflow:scroll that have scrollable content
        const findScrollableElement = (container: Element): Element | null => {
            // Check children with overflow auto/scroll
            const scrollableChildren = container.querySelectorAll("*");
            for (const child of scrollableChildren) {
                const style = window.getComputedStyle(child);
                const isScrollable =
                    style.overflowY === "auto" || style.overflowY === "scroll";
                const hasScrollableContent =
                    child.scrollHeight > child.clientHeight;

                if (isScrollable && hasScrollableContent) {
                    return child;
                }
            }

            // Fall back to the container itself if it's scrollable
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

        const scrollableElement = findScrollableElement(dialogContent);
        if (!scrollableElement) return;

        const scrollAmount = 150; // pixels to scroll per key press
        const currentScroll = scrollableElement.scrollTop;
        const newScroll =
            direction === "down"
                ? currentScroll + scrollAmount
                : currentScroll - scrollAmount;

        scrollableElement.scrollTo({
            top: Math.max(0, newScroll),
            behavior: "smooth",
        });
    }, []);

    // Click a button by aria-label or title within the appropriate container
    const clickActionButton = useCallback(
        (actionKey: string) => {
            const container = isDialogOpen
                ? document.querySelector("[role='dialog']")
                : document.querySelector("[data-highlighted='true']");

            if (!container) return;

            // Find by aria-label first, then fall back to title
            let clickable = container.querySelector(
                `button[aria-label="${actionKey}"], a[aria-label="${actionKey}"]`,
            ) as HTMLElement | null;

            if (!clickable) {
                clickable = container.querySelector(
                    `button[title="${actionKey}"], a[title="${actionKey}"]`,
                ) as HTMLElement | null;
            }

            if (clickable && !(clickable as HTMLButtonElement).disabled) {
                clickable.click();
            }
        },
        [isDialogOpen],
    );

    const handleKeyDown = useCallback(
        (event: KeyboardEvent) => {
            if (shouldIgnoreKeyEvent(event)) {
                return;
            }

            // Handle dialog-specific navigation
            if (isDialogOpen) {
                switch (event.key) {
                    case "Tab":
                    case "n":
                        // Tab/n key cycles through tabs (round robin)
                        handleTabNavigation();
                        event.preventDefault();
                        return;
                    case "j":
                    case "ArrowDown":
                        // Scroll dialog content down
                        handleDialogScroll("down");
                        event.preventDefault();
                        return;
                    case "k":
                    case "ArrowUp":
                        // Scroll dialog content up
                        handleDialogScroll("up");
                        event.preventDefault();
                        return;
                    case "h":
                    case "ArrowLeft":
                        // Tab navigation: h/ArrowLeft = left
                        handleTabNavigationDirection("left");
                        event.preventDefault();
                        return;
                    case "l":
                    case "ArrowRight":
                        // Tab navigation: l/ArrowRight = right
                        handleTabNavigationDirection("right");
                        event.preventDefault();
                        return;
                    case "Enter":
                    case " ":
                    case "i":
                        // Close the dialog by clicking the close button
                        clickActionButton("close");
                        event.preventDefault();
                        return;
                    case "Escape":
                        // Close dialog (already handled by MUI Dialog)
                        return;
                    case "f":
                        // Toggle fullscreen (dialog only)
                        clickActionButton("toggle fullscreen");
                        event.preventDefault();
                        return;
                }
            } else {
                // Handle result list navigation
                switch (event.key) {
                    case "Escape":
                        // Unselect the highlighted card
                        if (highlightedIndex !== null) {
                            dispatch(setHighlightedIndex(null));
                            event.preventDefault();
                        }
                        return;
                    case "j":
                    case "ArrowDown":
                        // Result navigation: j/ArrowDown = down
                        handleResultNavigation("down");
                        event.preventDefault();
                        return;
                    case "k":
                    case "ArrowUp":
                        // Result navigation: k/ArrowUp = up
                        handleResultNavigation("up");
                        event.preventDefault();
                        return;
                    case "Enter":
                    case " ":
                    case "i":
                        // Open preview dialog for highlighted result
                        clickActionButton("preview");
                        event.preventDefault();
                        return;
                    case "/":
                        // Focus the search input (vim-style)
                        {
                            const searchInput = document.querySelector(
                                "[data-search-input]",
                            ) as HTMLInputElement | null;
                            if (searchInput) {
                                searchInput.focus();
                                event.preventDefault();
                            }
                        }
                        return;
                }
            }

            // Shared action shortcuts (work in both dialog and result list contexts)
            switch (event.key) {
                case "c":
                    clickActionButton("share");
                    event.preventDefault();
                    return;
                case "o":
                    clickActionButton("open");
                    event.preventDefault();
                    return;
                case "d":
                    clickActionButton("download");
                    event.preventDefault();
                    return;
                case "r":
                    clickActionButton("re-index");
                    event.preventDefault();
                    return;
                case "s":
                    clickActionButton("summarize");
                    event.preventDefault();
                    return;
                case "t":
                    clickActionButton("tags-input");
                    event.preventDefault();
                    return;
                case "T":
                    clickActionButton("translate");
                    event.preventDefault();
                    return;
            }
        },
        [
            shouldIgnoreKeyEvent,
            isDialogOpen,
            highlightedIndex,
            dispatch,
            handleTabNavigation,
            handleTabNavigationDirection,
            handleDialogScroll,
            handleResultNavigation,
            clickActionButton,
        ],
    );

    useEffect(() => {
        document.addEventListener("keydown", handleKeyDown);
        return () => {
            document.removeEventListener("keydown", handleKeyDown);
        };
    }, [handleKeyDown]);
}
