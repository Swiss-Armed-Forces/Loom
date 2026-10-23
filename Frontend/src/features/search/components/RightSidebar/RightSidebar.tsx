import { Clear, Search, Close } from "@mui/icons-material";
import {
    Drawer,
    IconButton,
    InputAdornment,
    InputBase,
    Typography,
    useMediaQuery,
} from "@mui/material";
import { useEffect, useRef, useState, memo } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    RightSidebarTab,
    selectQuery,
    selectRightSidebarOpen,
    selectRightSidebarTab,
    selectRightSidebarWidth,
    selectTotalFiles,
    setRightSidebarWidth,
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
import { clampSidebarWidth } from "@features/search/components/sidebarWidth";
import { FileDetailView } from "@features/search/views/FileDetail/FileDetailView";
import { FolderView } from "@features/search/views/Folder/FolderView";
import { StatisticsView } from "@features/search/views/Statistics/StatisticsView";

import styles from "./RightSidebar.module.css";

export const RightSidebar = memo(() => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();
    const isOpen = useAppSelector(selectRightSidebarOpen);
    const activeTab = useAppSelector(selectRightSidebarTab);
    const numberOfResults = useAppSelector(selectTotalFiles);
    const searchQuery = useAppSelector(selectQuery);
    const { activeTourStepId, isTourActive } = useTour();
    const tourTab = getTourRightTab(isTourActive, activeTourStepId);
    const effectiveIsOpen = tourTab !== undefined ? tourTab !== null : isOpen;
    const effectiveActiveTab = tourTab ?? activeTab;
    const isMobile = useMediaQuery("(max-width:600px)");

    const storedWidth = useAppSelector(selectRightSidebarWidth);
    const [width, setWidth] = useState(() => clampSidebarWidth(storedWidth));
    const sidebarRef = useRef<HTMLDivElement>(null);
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
        setIsDragging(true);

        // The width is written straight to the element while dragging. Going
        // through React state would re-render the whole sidebar — folder tree,
        // chat panel, file detail — once per pointer move.
        const onMouseMove = (ev: MouseEvent) => {
            const newWidth = clampSidebarWidth(
                startWidth + startX - ev.clientX,
            );
            widthRef.current = newWidth;
            if (sidebarRef.current) {
                sidebarRef.current.style.width = `${newWidth}px`;
            }
        };

        const onMouseUp = () => {
            setIsDragging(false);
            setWidth(widthRef.current);
            dispatch(setRightSidebarWidth(widthRef.current));
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
                    <FileDetailView />
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
            ref={sidebarRef}
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
});

RightSidebar.displayName = "RightSidebar";
