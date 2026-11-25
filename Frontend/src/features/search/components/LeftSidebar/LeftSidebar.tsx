import { AddComment, Close, Forum, VisibilityOff } from "@mui/icons-material";
import {
    Drawer,
    IconButton,
    Tooltip,
    Typography,
    useMediaQuery,
} from "@mui/material";
import { useEffect, useRef, useState, memo } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    LeftSidebarPanel,
    selectHighlightedQueryId,
    selectLeftSidebarPanel,
    selectLeftSidebarWidth,
    selectQuery,
    setLeftSidebarPanel,
    setLeftSidebarWidth,
} from "@app/slices/searchSlice";
import { getTourLeftPanel } from "@app/tours/tourScene";
import { useTour } from "@app/tours/useTour";
import type { SearchQuery } from "@features/common/utils/model";
import { clampSidebarWidth } from "@features/search/components/sidebarWidth";
import { TagsPanel } from "@features/search/components/TagsList/TagsPanel";
import { FolderView } from "@features/search/views/Folder/FolderView";
import { FolderViewOptionsButton } from "@features/search/views/Folder/FolderViewOptions";
import { PathDepthStatus } from "@features/search/views/Folder/PathDepthStatus";

import { Chatbot } from "../ChatMenu/Chatbot";
import { useChatbot } from "../ChatMenu/useChatbot";
import { Customization } from "../Customization/Customization";
import { CustomQueriesList } from "../CustomQueries/CustomQueries";

import styles from "./LeftSidebar.module.css";

const GLOBAL_FOLDER_QUERY: SearchQuery = {
    id: null,
    query: "*",
    keepAlive: null,
    sortField: null,
    sortDirection: null,
    sortId: null,
    pageSize: null,
};

// Panels that render their own filter bar and scroll their own body. The frame
// must not scroll underneath them, or the bar would scroll away with the list.
const SELF_SCROLLING_PANELS = new Set<LeftSidebarPanel>([
    LeftSidebarPanel.FOLDER,
    LeftSidebarPanel.TAGS,
    LeftSidebarPanel.QUERIES,
]);

const PANEL_TITLES: Record<LeftSidebarPanel, string> = {
    [LeftSidebarPanel.FOLDER]: "toolbar.views.folder",
    [LeftSidebarPanel.TAGS]: "sideMenu.tags",
    [LeftSidebarPanel.QUERIES]: "sideMenu.savedQueries.title",
    [LeftSidebarPanel.CUSTOMIZATION]: "sideMenu.customizations.title",
    [LeftSidebarPanel.CHAT]: "AI Assistant",
};

// Propless and rendered from a parent that re-renders on unrelated store
// changes, so memo is what keeps one highlight change from sweeping the
// whole subtree. Its own selector subscriptions still re-render it.
export const LeftSidebar = memo(() => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();
    const activePanel = useAppSelector(selectLeftSidebarPanel);
    const { activeTourStepId, isTourActive } = useTour();
    const tourPanel = getTourLeftPanel(isTourActive, activeTourStepId);
    const effectiveActivePanel =
        tourPanel !== undefined ? tourPanel : activePanel;
    const highlightedQueryId = useAppSelector(selectHighlightedQueryId);
    const reduxQuery = useAppSelector(selectQuery);

    const isChatPanel = effectiveActivePanel === LeftSidebarPanel.CHAT;
    const chatbot = useChatbot(isChatPanel);

    const isMobile = useMediaQuery("(max-width:600px)");
    const storedWidth = useAppSelector(selectLeftSidebarWidth);
    const [width, setWidth] = useState(() => clampSidebarWidth(storedWidth));
    const sidebarRef = useRef<HTMLDivElement>(null);
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

        // The width is written straight to the element while dragging. Going
        // through React state would re-render the whole sidebar — folder tree,
        // chat panel, file detail — once per pointer move.
        const onMouseMove = (ev: MouseEvent) => {
            const newWidth = clampSidebarWidth(
                startWidth + ev.clientX - startX,
            );
            widthRef.current = newWidth;
            if (sidebarRef.current) {
                sidebarRef.current.style.width = `${newWidth}px`;
            }
        };

        const onMouseUp = () => {
            setIsDragging(false);
            setWidth(widthRef.current);
            dispatch(setLeftSidebarWidth(widthRef.current));
            document.removeEventListener("mousemove", onMouseMove);
            document.removeEventListener("mouseup", onMouseUp);
            dragHandlersRef.current = null;
        };

        dragHandlersRef.current = { onMouseMove, onMouseUp };
        document.addEventListener("mousemove", onMouseMove);
        document.addEventListener("mouseup", onMouseUp);
    };

    const renderPanelContent = () => {
        switch (effectiveActivePanel) {
            case LeftSidebarPanel.FOLDER:
                return (
                    <FolderView
                        searchQuery={GLOBAL_FOLDER_QUERY}
                        filterTour="sidebar-folder-filter"
                        persistExpansion={true}
                        refreshKey={reduxQuery?.id ?? null}
                    />
                );
            case LeftSidebarPanel.TAGS:
                return <TagsPanel />;
            case LeftSidebarPanel.QUERIES:
                return (
                    <CustomQueriesList
                        hideHeader
                        filterable
                        highlightedQueryId={highlightedQueryId}
                    />
                );
            case LeftSidebarPanel.CUSTOMIZATION:
                return <Customization />;
            case LeftSidebarPanel.CHAT:
                return <Chatbot chatbot={chatbot} />;
            default:
                return null;
        }
    };

    const sidebarWidth = effectiveActivePanel === null ? 0 : width;
    const panelScrollsItself =
        effectiveActivePanel !== null &&
        SELF_SCROLLING_PANELS.has(effectiveActivePanel);

    const panelContent =
        effectiveActivePanel !== null ? (
            <>
                <div className={styles.header}>
                    {isChatPanel ? (
                        <Typography
                            noWrap
                            sx={{
                                flex: 1,
                                minWidth: 0,
                                fontSize: "0.75rem",
                                fontWeight: 600,
                                opacity: 0.7,
                            }}
                        >
                            {chatbot.showHistory
                                ? "All Conversations"
                                : chatbot.contextLabel}
                        </Typography>
                    ) : (
                        <Typography className={styles.headerTitle}>
                            {t(PANEL_TITLES[effectiveActivePanel])}
                        </Typography>
                    )}
                    {isChatPanel && (
                        <>
                            <Tooltip
                                title={
                                    chatbot.showHistory
                                        ? "Hide from the conversation list (not available in list view)"
                                        : chatbot.isHidden
                                          ? "Show in the conversation list"
                                          : "Hide from the conversation list (the conversation stays stored)"
                                }
                            >
                                <IconButton
                                    size="small"
                                    disabled={
                                        chatbot.showHistory ||
                                        chatbot.isHiddenPending
                                    }
                                    onClick={
                                        chatbot.isHidden
                                            ? chatbot.handleUnhideActiveContext
                                            : chatbot.handleHideActiveContext
                                    }
                                    color={
                                        chatbot.isHidden ? "warning" : "default"
                                    }
                                >
                                    <VisibilityOff fontSize="small" />
                                </IconButton>
                            </Tooltip>
                            <Tooltip title="All conversations">
                                <IconButton
                                    size="small"
                                    onClick={chatbot.handleToggleHistory}
                                    color={
                                        chatbot.showHistory
                                            ? "primary"
                                            : "default"
                                    }
                                    data-tour="chat-history-button"
                                >
                                    <Forum fontSize="small" />
                                </IconButton>
                            </Tooltip>
                            <Tooltip title="New chat">
                                <IconButton
                                    size="small"
                                    onClick={chatbot.handleNewChat}
                                    data-tour="chat-new-button"
                                >
                                    <AddComment fontSize="small" />
                                </IconButton>
                            </Tooltip>
                        </>
                    )}
                    {effectiveActivePanel === LeftSidebarPanel.FOLDER && (
                        <FolderViewOptionsButton expansionKey="global" />
                    )}
                    <IconButton
                        size="small"
                        onClick={() => {
                            if (!isTourActive)
                                dispatch(setLeftSidebarPanel(null));
                        }}
                    >
                        <Close fontSize="small" />
                    </IconButton>
                </div>
                {effectiveActivePanel === LeftSidebarPanel.FOLDER && (
                    <PathDepthStatus expansionKey="global" />
                )}
                {/* The folder tree and the lists in here handle their own arrow
                    keys. Marking the pane keeps the document-level result
                    shortcuts from moving the result highlight at the same
                    time; letter shortcuts still reach the results. */}
                <div
                    className={`${styles.content} ${panelScrollsItself ? styles.contentUnscrolled : ""}`}
                    data-keynav-ignore
                    style={
                        isChatPanel
                            ? { overflow: "hidden", padding: 0 }
                            : undefined
                    }
                    data-tour={
                        activeTourStepId
                            ? `sidebar-${activeTourStepId}`
                            : undefined
                    }
                >
                    {renderPanelContent()}
                </div>
            </>
        ) : null;

    if (isMobile) {
        return (
            <Drawer
                open={effectiveActivePanel !== null}
                onClose={() => {
                    if (!isTourActive) dispatch(setLeftSidebarPanel(null));
                }}
                variant="temporary"
                anchor="left"
                slotProps={{
                    paper: {
                        sx: {
                            width: "85vw",
                            maxWidth: "360px",
                            display: "flex",
                            flexDirection: "column",
                        },
                    },
                }}
            >
                {panelContent}
            </Drawer>
        );
    }

    return (
        <div
            ref={sidebarRef}
            className={`${styles.leftSidebar} ${isDragging ? styles.dragging : ""}`}
            style={{ width: sidebarWidth }}
        >
            {panelContent}
            {effectiveActivePanel !== null && (
                <div
                    className={`${styles.dragHandle} ${isDragging ? styles.dragging : ""}`}
                    onMouseDown={handleMouseDown}
                />
            )}
        </div>
    );
});

LeftSidebar.displayName = "LeftSidebar";
