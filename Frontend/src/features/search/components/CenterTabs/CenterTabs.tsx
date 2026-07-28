import { Close, Search } from "@mui/icons-material";
import {
    Box,
    Divider,
    IconButton,
    Tab,
    Tabs,
    useMediaQuery,
} from "@mui/material";
import { useRef, useState } from "react";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    closeFileTabThunk,
    selectActiveTabFileId,
    selectFiles,
    selectLoadedFiles,
    selectOpenFileTabs,
    selectTotalFiles,
    setActiveTabFileId,
} from "@app/slices/searchSlice";
import { useTour } from "@app/tours/useTour";
import { FileDetailTab } from "@features/common/utils/enums";
import { ScrollToTop } from "@features/search/components";
import { SearchResults } from "@features/search/views/SearchResults";

import { FileDetailPanel } from "../FileDetailPanel/FileDetailPanel";

import styles from "./CenterTabs.module.css";
import { shouldShowFilePanel, shouldShowSearchPanel } from "./panelVisibility";

const TOUR_DETAIL_STEP_IDS = new Set([
    "document-detail",
    "detail-rendered",
    "detail-translations",
    "detail-highlights",
    "detail-raw",
]);

const TOUR_DETAIL_TAB: Partial<Record<string, FileDetailTab>> = {
    "detail-translations": FileDetailTab.Translations,
    "detail-highlights": FileDetailTab.Highlights,
    "detail-raw": FileDetailTab.RAW,
};

const SEARCH_TAB = "__search__";

export const CenterTabs = () => {
    const dispatch = useAppDispatch();
    const openFileTabs = useAppSelector(selectOpenFileTabs);
    const activeTabFileId = useAppSelector(selectActiveTabFileId);
    const files = useAppSelector(selectFiles);
    const { activeTourStepId, isTourActive, tourDetailFileId } = useTour();

    const totalFiles = useAppSelector(selectTotalFiles);
    const loadedFiles = useAppSelector(selectLoadedFiles);

    const isMobile = useMediaQuery("(max-width:600px)");
    const scrollRef = useRef<HTMLDivElement>(null);
    const [hasScrollOffset, setHasScrollOffset] = useState(false);
    const showTourDocumentDetail =
        isTourActive &&
        TOUR_DETAIL_STEP_IDS.has(activeTourStepId ?? "") &&
        tourDetailFileId !== null;
    const tourDetailTab =
        (activeTourStepId ? TOUR_DETAIL_TAB[activeTourStepId] : undefined) ??
        FileDetailTab.Rendered;
    const showSearchPanel = showTourDocumentDetail
        ? false
        : shouldShowSearchPanel(activeTabFileId, isTourActive);

    const handleFileTabChange = (_: React.SyntheticEvent, newValue: string) => {
        dispatch(setActiveTabFileId(newValue));
    };

    return (
        <div className={styles.centerTabs}>
            <div className={styles.tabBar} data-tour="results-tabs">
                {/* Pinned Results tab — always visible, never scrolls */}
                <Tabs
                    value={showSearchPanel ? SEARCH_TAB : false}
                    data-tour="search-workspace"
                >
                    <Tab
                        value={SEARCH_TAB}
                        label={
                            <span className={styles.resultsTabLabel}>
                                <Search sx={{ fontSize: 14 }} />
                                Results
                                {totalFiles > 0 && (
                                    <span className={styles.resultsTabCount}>
                                        {loadedFiles}/{totalFiles}
                                    </span>
                                )}
                            </span>
                        }
                        onClick={() => dispatch(setActiveTabFileId(null))}
                    />
                </Tabs>

                {showTourDocumentDetail && (
                    <>
                        <Divider
                            orientation="vertical"
                            flexItem
                            sx={{ my: 1 }}
                        />
                        <Tabs value={tourDetailFileId} sx={{ flex: 1 }}>
                            <Tab
                                value={tourDetailFileId}
                                label={
                                    files[tourDetailFileId]?.preview?.path
                                        .split("/")
                                        .at(-1) ?? tourDetailFileId
                                }
                            />
                        </Tabs>
                    </>
                )}

                {/* Scrollable file tabs */}
                {!showTourDocumentDetail && openFileTabs.length > 0 && (
                    <>
                        <Divider
                            orientation="vertical"
                            flexItem
                            sx={{ my: 1 }}
                        />
                        <Tabs
                            value={activeTabFileId ?? false}
                            onChange={handleFileTabChange}
                            variant="scrollable"
                            scrollButtons="auto"
                            sx={{ flex: 1 }}
                        >
                            {openFileTabs.map((tab) => {
                                const preview = files[tab.fileId]?.preview;
                                const name =
                                    preview?.path.split("/").at(-1) ??
                                    tab.fileId;
                                const isFlagged = preview?.flagged ?? false;
                                const isUnseen = preview?.seen === false;
                                return (
                                    <Tab
                                        key={tab.fileId}
                                        value={tab.fileId}
                                        onMouseDown={(e) => {
                                            if (e.button === 1) {
                                                e.preventDefault();
                                                dispatch(
                                                    closeFileTabThunk(
                                                        tab.fileId,
                                                    ),
                                                );
                                            }
                                        }}
                                        label={
                                            <span
                                                className={styles.fileTabLabel}
                                            >
                                                <span
                                                    className={
                                                        styles.fileTabName
                                                    }
                                                    title={
                                                        preview?.path ??
                                                        tab.fileId
                                                    }
                                                    style={{
                                                        ...(isFlagged && {
                                                            color: "var(--mui-palette-error-main)",
                                                        }),
                                                        ...(isUnseen && {
                                                            fontWeight: "bold",
                                                        }),
                                                    }}
                                                >
                                                    {name}
                                                </span>
                                                <IconButton
                                                    component="span"
                                                    size={
                                                        isMobile
                                                            ? "medium"
                                                            : "small"
                                                    }
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        dispatch(
                                                            closeFileTabThunk(
                                                                tab.fileId,
                                                            ),
                                                        );
                                                    }}
                                                    aria-label="close tab"
                                                    sx={{
                                                        transition:
                                                            "opacity 0.2s ease",
                                                        "&:hover": {
                                                            opacity: 0.7,
                                                        },
                                                    }}
                                                >
                                                    <Close
                                                        sx={{
                                                            fontSize: isMobile
                                                                ? 16
                                                                : 12,
                                                        }}
                                                    />
                                                </IconButton>
                                            </span>
                                        }
                                    />
                                );
                            })}
                        </Tabs>
                    </>
                )}
            </div>

            {/* Search results panel — always mounted, hidden when inactive */}
            <div
                className={styles.searchPanel}
                style={{
                    display: showSearchPanel ? "flex" : "none",
                }}
                onScroll={(e) =>
                    setHasScrollOffset(
                        (e.target as HTMLDivElement).scrollTop > 0,
                    )
                }
                ref={scrollRef}
            >
                <SearchResults />
                <ScrollToTop
                    visible={hasScrollOffset}
                    onClick={() => scrollRef.current?.scrollTo(0, 0)}
                />
            </div>

            {showTourDocumentDetail && (
                <Box
                    className={styles.filePanel}
                    data-tour="document-detail"
                    sx={{ display: "flex" }}
                >
                    <FileDetailPanel
                        fileId={tourDetailFileId}
                        detailTab={tourDetailTab}
                        isActive={false}
                    />
                </Box>
            )}

            {/* File detail panels — each mounted once, hidden when inactive */}
            {openFileTabs.map((tab) => (
                <Box
                    key={tab.fileId}
                    className={styles.filePanel}
                    sx={{
                        display: shouldShowFilePanel(
                            tab.fileId,
                            activeTabFileId,
                            isTourActive,
                        )
                            ? "flex"
                            : "none",
                    }}
                >
                    <FileDetailPanel
                        fileId={tab.fileId}
                        detailTab={tab.detailTab}
                        isActive={activeTabFileId === tab.fileId}
                    />
                </Box>
            ))}
        </div>
    );
};
