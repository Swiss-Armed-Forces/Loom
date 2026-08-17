import { Clear, Search, Close } from "@mui/icons-material";
import {
    Drawer,
    IconButton,
    InputAdornment,
    InputBase,
    Typography,
    useMediaQuery,
} from "@mui/material";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import { selectLastFileDetailTab } from "@app/slices/commonSlice";
import {
    RightSidebarTab,
    selectHighlightedFileId,
    selectQuery,
    selectRightSidebarOpen,
    selectRightSidebarTab,
    selectTotalFiles,
    toggleRightSidebar,
} from "@app/slices/searchSlice";
import { getTourRightTab } from "@app/tours/tourScene";
import { useTour } from "@app/tours/useTour";
import {
    AddTagsButton,
    CreateArchiveButton,
    ImageDescriptionButton,
    ReIndexButton,
    SummaryButton,
    TranslationButton,
    UpdateFlaggedButton,
    UpdateHiddenButton,
    UpdateSeenButton,
} from "@features/search/components/FileActionButtons";
import { FileDetailPanel } from "@features/search/components/FileDetailPanel/FileDetailPanel";
import { FolderView } from "@features/search/views/Folder/FolderView";
import { StatisticsView } from "@features/search/views/Statistics/StatisticsView";

import styles from "./RightSidebar.module.css";

const MIN_WIDTH = 14 * 16;
const DEFAULT_WIDTH = 28 * 16;
const CENTER_MIN_WIDTH = 20 * 16;
const WIDTH_STORAGE_KEY = "RIGHT_SIDEBAR_WIDTH";

const loadWidth = (): number => {
    const stored = localStorage.getItem(WIDTH_STORAGE_KEY);
    if (stored) {
        const n = parseInt(stored, 10);
        const effectiveMax = Math.max(
            MIN_WIDTH,
            window.innerWidth - CENTER_MIN_WIDTH,
        );
        if (!isNaN(n) && n >= MIN_WIDTH) return Math.min(n, effectiveMax);
    }
    return DEFAULT_WIDTH;
};

export const RightSidebar = () => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();
    const isOpen = useAppSelector(selectRightSidebarOpen);
    const activeTab = useAppSelector(selectRightSidebarTab);
    const numberOfResults = useAppSelector(selectTotalFiles);
    const searchQuery = useAppSelector(selectQuery);
    const highlightedFileId = useAppSelector(selectHighlightedFileId);
    const lastFileDetailTab = useAppSelector(selectLastFileDetailTab);
    const { activeTourStepId, isTourActive } = useTour();
    const tourTab = getTourRightTab(isTourActive, activeTourStepId);
    const effectiveIsOpen = tourTab !== undefined ? tourTab !== null : isOpen;
    const effectiveActiveTab = tourTab ?? activeTab;
    const isMobile = useMediaQuery("(max-width:600px)");

    const [width, setWidth] = useState(loadWidth);
    const [isDragging, setIsDragging] = useState(false);
    const [folderFilterText, setFolderFilterText] = useState("");
    const widthRef = useRef(width);
    const dragHandlersRef = useRef<{
        onMouseMove: (ev: MouseEvent) => void;
        onMouseUp: () => void;
    } | null>(null);

    useEffect(() => {
        if (activeTab !== RightSidebarTab.FOLDER) setFolderFilterText("");
    }, [activeTab]);

    // Remove any in-flight drag listeners when the component unmounts
    useEffect(() => {
        return () => {
            if (dragHandlersRef.current) {
                document.removeEventListener(
                    "mousemove",
                    dragHandlersRef.current.onMouseMove,
                );
                document.removeEventListener(
                    "mouseup",
                    dragHandlersRef.current.onMouseUp,
                );
                dragHandlersRef.current = null;
            }
        };
    }, []);

    const handleMouseDown = (e: React.MouseEvent) => {
        e.preventDefault();
        const startX = e.clientX;
        const startWidth = widthRef.current;
        const effectiveMax = Math.max(
            MIN_WIDTH,
            window.innerWidth - CENTER_MIN_WIDTH,
        );
        setIsDragging(true);

        const onMouseMove = (ev: MouseEvent) => {
            const newWidth = Math.min(
                effectiveMax,
                Math.max(MIN_WIDTH, startWidth + startX - ev.clientX),
            );
            widthRef.current = newWidth;
            setWidth(newWidth);
        };

        const onMouseUp = () => {
            setIsDragging(false);
            localStorage.setItem(WIDTH_STORAGE_KEY, String(widthRef.current));
            document.removeEventListener("mousemove", onMouseMove);
            document.removeEventListener("mouseup", onMouseUp);
            dragHandlersRef.current = null;
        };

        dragHandlersRef.current = { onMouseMove, onMouseUp };
        document.addEventListener("mousemove", onMouseMove);
        document.addEventListener("mouseup", onMouseUp);
    };

    const sidebarWidth = effectiveIsOpen ? width : 0;

    const tabTitle =
        effectiveActiveTab === RightSidebarTab.STATISTICS
            ? t("toolbar.views.statistics")
            : effectiveActiveTab === RightSidebarTab.FOLDER
              ? t("toolbar.views.filteredFolder")
              : effectiveActiveTab === RightSidebarTab.BULK_ACTIONS
                ? t("sideMenu.bulkActions")
                : t("toolbar.views.fileDetail");

    const sidebarContent = (
        <>
            <div className={styles.header}>
                <Typography className={styles.headerTitle}>
                    {tabTitle}
                </Typography>
                <IconButton
                    size="small"
                    onClick={() => {
                        if (!isTourActive) dispatch(toggleRightSidebar());
                    }}
                >
                    <Close fontSize="small" />
                </IconButton>
            </div>
            {effectiveActiveTab === RightSidebarTab.FOLDER && (
                <div className={styles.filterBar}>
                    <InputBase
                        className={styles.filterInput}
                        value={folderFilterText}
                        onChange={(e) => setFolderFilterText(e.target.value)}
                        placeholder={t("folderView.filterPlaceholder")}
                        inputProps={{ "aria-label": "filter" }}
                        startAdornment={
                            <InputAdornment position="start">
                                <Search
                                    fontSize="small"
                                    className={styles.filterIcon}
                                />
                            </InputAdornment>
                        }
                        endAdornment={
                            folderFilterText ? (
                                <InputAdornment position="end">
                                    <IconButton
                                        size="small"
                                        onClick={() => setFolderFilterText("")}
                                        edge="end"
                                    >
                                        <Clear
                                            fontSize="small"
                                            className={styles.filterIcon}
                                        />
                                    </IconButton>
                                </InputAdornment>
                            ) : null
                        }
                    />
                </div>
            )}
            <div
                className={styles.content}
                data-tour={
                    activeTourStepId ? `sidebar-${activeTourStepId}` : undefined
                }
            >
                {effectiveActiveTab === RightSidebarTab.STATISTICS ? (
                    <StatisticsView />
                ) : effectiveActiveTab === RightSidebarTab.FOLDER ? (
                    <FolderView
                        expansionKey="filtered"
                        filter={folderFilterText}
                    />
                ) : effectiveActiveTab === RightSidebarTab.BULK_ACTIONS ? (
                    <div className={styles.bulkActionButtons}>
                        <UpdateFlaggedButton
                            buttonFullWidth
                            disabled={numberOfResults === 0}
                        />
                        <UpdateSeenButton
                            buttonFullWidth
                            disabled={numberOfResults === 0}
                        />
                        <AddTagsButton disabled={numberOfResults === 0} />
                        <TranslationButton disabled={numberOfResults === 0} />
                        <SummaryButton disabled={numberOfResults === 0} />
                        <ImageDescriptionButton
                            disabled={numberOfResults === 0}
                        />
                        <ReIndexButton disabled={numberOfResults === 0} />
                        <UpdateHiddenButton
                            buttonFullWidth
                            disabled={numberOfResults === 0}
                        />
                        <CreateArchiveButton
                            searchQuery={searchQuery}
                            disabled={numberOfResults === 0}
                        />
                    </div>
                ) : effectiveActiveTab === RightSidebarTab.FILE_DETAIL ? (
                    highlightedFileId ? (
                        <FileDetailPanel
                            fileId={highlightedFileId}
                            detailTab={lastFileDetailTab}
                            isActive={effectiveIsOpen}
                            compact
                        />
                    ) : (
                        <Typography sx={{ p: 2, color: "text.secondary" }}>
                            {t("toolbar.views.fileDetailEmpty")}
                        </Typography>
                    )
                ) : null}
            </div>
        </>
    );

    if (isMobile) {
        return (
            <Drawer
                open={effectiveIsOpen}
                onClose={() => {
                    if (!isTourActive) dispatch(toggleRightSidebar());
                }}
                variant="temporary"
                anchor="right"
                slotProps={{
                    paper: {
                        sx: {
                            width: "90vw",
                            maxWidth: "400px",
                            display: "flex",
                            flexDirection: "column",
                        },
                    },
                }}
            >
                {sidebarContent}
            </Drawer>
        );
    }

    return (
        <div
            className={`${styles.rightSidebar} ${isDragging ? styles.dragging : ""}`}
            style={{ width: sidebarWidth }}
        >
            {effectiveIsOpen && (
                <div
                    className={`${styles.dragHandle} ${isDragging ? styles.dragging : ""}`}
                    onMouseDown={handleMouseDown}
                />
            )}
            {effectiveIsOpen && sidebarContent}
        </div>
    );
};
