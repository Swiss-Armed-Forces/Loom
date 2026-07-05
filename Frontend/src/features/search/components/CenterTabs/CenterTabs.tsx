import { Close, Search } from "@mui/icons-material";
import { Box, Divider, IconButton, Tab, Tabs } from "@mui/material";
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
import { ScrollToTop } from "@features/search/components";
import { SearchResults } from "@features/search/views/SearchResults";

import { FileDetailPanel } from "../FileDetailPanel/FileDetailPanel";

import styles from "./CenterTabs.module.css";

const SEARCH_TAB = "__search__";

export const CenterTabs = () => {
    const dispatch = useAppDispatch();
    const openFileTabs = useAppSelector(selectOpenFileTabs);
    const activeTabFileId = useAppSelector(selectActiveTabFileId);
    const files = useAppSelector(selectFiles);

    const totalFiles = useAppSelector(selectTotalFiles);
    const loadedFiles = useAppSelector(selectLoadedFiles);

    const scrollRef = useRef<HTMLDivElement>(null);
    const [hasScrollOffset, setHasScrollOffset] = useState(false);

    const handleFileTabChange = (_: React.SyntheticEvent, newValue: string) => {
        dispatch(setActiveTabFileId(newValue));
    };

    return (
        <div className={styles.centerTabs}>
            <div className={styles.tabBar}>
                {/* Pinned Results tab — always visible, never scrolls */}
                <Tabs value={activeTabFileId === null ? SEARCH_TAB : false}>
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

                {/* Scrollable file tabs */}
                {openFileTabs.length > 0 && (
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
                                                    size="small"
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
                                                        sx={{ fontSize: 12 }}
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
                    display: activeTabFileId === null ? "flex" : "none",
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

            {/* File detail panels — each mounted once, hidden when inactive */}
            {openFileTabs.map((tab) => (
                <Box
                    key={tab.fileId}
                    className={styles.filePanel}
                    sx={{
                        display:
                            activeTabFileId === tab.fileId ? "flex" : "none",
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
