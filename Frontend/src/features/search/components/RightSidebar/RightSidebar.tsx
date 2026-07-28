import { Close } from "@mui/icons-material";
import { Drawer, IconButton, Tab, Tabs, useMediaQuery } from "@mui/material";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    RightSidebarTab,
    selectRightSidebarOpen,
    selectRightSidebarTab,
    setRightSidebarTab,
    toggleRightSidebar,
} from "@app/slices/searchSlice";
import { getTourRightTab } from "@app/tours/tourScene";
import { useTour } from "@app/tours/useTour";
import { Chatbot } from "@features/search/components/ChatMenu/Chatbot";
import { StatisticsView } from "@features/search/views/Statistics/StatisticsView";

import styles from "./RightSidebar.module.css";

const MIN_WIDTH = 14 * 16;
const DEFAULT_WIDTH = 28 * 16;
const MAX_WIDTH = 40 * 16;
const WIDTH_STORAGE_KEY = "RIGHT_SIDEBAR_WIDTH";

const loadWidth = (): number => {
    const stored = localStorage.getItem(WIDTH_STORAGE_KEY);
    if (stored) {
        const n = parseInt(stored, 10);
        if (!isNaN(n) && n >= MIN_WIDTH && n <= MAX_WIDTH) return n;
    }
    return DEFAULT_WIDTH;
};

export const RightSidebar = () => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();
    const isOpen = useAppSelector(selectRightSidebarOpen);
    const activeTab = useAppSelector(selectRightSidebarTab);
    const { activeTourStepId, isTourActive } = useTour();
    const tourTab = getTourRightTab(isTourActive, activeTourStepId);
    const effectiveIsOpen = tourTab !== undefined ? tourTab !== null : isOpen;
    const effectiveActiveTab = tourTab ?? activeTab;
    const isMobile = useMediaQuery("(max-width:600px)");

    const [width, setWidth] = useState(loadWidth);
    const [isDragging, setIsDragging] = useState(false);
    const widthRef = useRef(width);
    const dragHandlersRef = useRef<{
        onMouseMove: (ev: MouseEvent) => void;
        onMouseUp: () => void;
    } | null>(null);

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

        const onMouseMove = (ev: MouseEvent) => {
            const newWidth = Math.min(
                MAX_WIDTH,
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

    const sidebarContent = (
        <>
            <div className={styles.header}>
                <Tabs
                    className={styles.tabs}
                    value={effectiveActiveTab}
                    onChange={(_, tab: RightSidebarTab) => {
                        if (!isTourActive) dispatch(setRightSidebarTab(tab));
                    }}
                    textColor="inherit"
                >
                    <Tab
                        value={RightSidebarTab.STATISTICS}
                        label={t("toolbar.views.statistics")}
                    />
                    <Tab value={RightSidebarTab.CHAT} label="Chatbot" />
                </Tabs>
                <IconButton
                    size="small"
                    onClick={() => {
                        if (!isTourActive) dispatch(toggleRightSidebar());
                    }}
                    sx={{ mr: 0.5 }}
                >
                    <Close fontSize="small" />
                </IconButton>
            </div>
            <div
                className={styles.content}
                data-tour={
                    activeTourStepId ? `sidebar-${activeTourStepId}` : undefined
                }
            >
                {effectiveActiveTab === RightSidebarTab.STATISTICS ? (
                    <StatisticsView />
                ) : (
                    <Chatbot />
                )}
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
