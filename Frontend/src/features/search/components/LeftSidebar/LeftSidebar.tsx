import {
    Check,
    Close,
    FlagOutlined,
    ImageSearch,
    MarkEmailUnreadOutlined,
    Search,
    SummarizeOutlined,
    Translate,
    YoutubeSearchedForOutlined,
} from "@mui/icons-material";
import {
    IconButton,
    InputAdornment,
    InputBase,
    List,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    Typography,
} from "@mui/material";
import { ReactNode, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    LeftSidebarPanel,
    selectAutoActionsPreferences,
    selectHighlightedQueryId,
    selectLeftSidebarPanel,
    selectQuery,
    selectTags,
    selectTotalFiles,
    setAutoActionPreference,
    setLeftSidebarPanel,
} from "@app/slices/searchSlice";
import {
    ReIndexButton,
    SummaryButton,
    TranslationButton,
    AddTagsButton,
    UpdateFlaggedButton,
    UpdateHiddenButton,
    UpdateSeenButton,
    CreateArchiveButton,
    ImageDescriptionButton,
} from "@features/search/components/FileActionButtons";
import { TagsList } from "@features/search/components/TagsList/TagsList";
import { FolderView } from "@features/search/views/Folder/FolderView";

import { CustomQueriesList } from "../CustomQueries/CustomQueries";

import styles from "./LeftSidebar.module.css";

const MIN_WIDTH = 14 * 16;
const DEFAULT_WIDTH = 20 * 16;
const MAX_WIDTH = 40 * 16;
const WIDTH_STORAGE_KEY = "LEFT_SIDEBAR_WIDTH";

const FILTERABLE_PANELS = new Set<LeftSidebarPanel>([
    LeftSidebarPanel.FOLDER,
    LeftSidebarPanel.TAGS,
    LeftSidebarPanel.QUERIES,
]);

const loadWidth = (): number => {
    const stored = localStorage.getItem(WIDTH_STORAGE_KEY);
    if (stored) {
        const n = parseInt(stored, 10);
        if (!isNaN(n) && n >= MIN_WIDTH && n <= MAX_WIDTH) return n;
    }
    return DEFAULT_WIDTH;
};

const PANEL_TITLES: Record<LeftSidebarPanel, string> = {
    [LeftSidebarPanel.FOLDER]: "toolbar.views.folder",
    [LeftSidebarPanel.TAGS]: "sideMenu.tags",
    [LeftSidebarPanel.QUERIES]: "sideMenu.savedQueries.title",
    [LeftSidebarPanel.BULK_ACTIONS]: "sideMenu.bulkActions",
    [LeftSidebarPanel.AUTO_ACTIONS]: "sideMenu.autoActions.title",
};

type BooleanAutoActionKey =
    | "markAsSeen"
    | "flag"
    | "reindex"
    | "translate"
    | "summarize"
    | "describeImage";

export const LeftSidebar = () => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();
    const activePanel = useAppSelector(selectLeftSidebarPanel);
    const numberOfResults = useAppSelector(selectTotalFiles);
    const searchQuery = useAppSelector(selectQuery);
    const tags = useAppSelector(selectTags);
    const preferences = useAppSelector(selectAutoActionsPreferences);
    const highlightedQueryId = useAppSelector(selectHighlightedQueryId);

    const [width, setWidth] = useState(loadWidth);
    const [isDragging, setIsDragging] = useState(false);
    const [filterText, setFilterText] = useState("");
    const widthRef = useRef(width);
    const dragHandlersRef = useRef<{
        onMouseMove: (ev: MouseEvent) => void;
        onMouseUp: () => void;
    } | null>(null);

    // Reset filter whenever the active panel changes
    useEffect(() => {
        setFilterText("");
    }, [activePanel]);

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
                Math.max(MIN_WIDTH, startWidth + ev.clientX - startX),
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

    const setPreference = (key: BooleanAutoActionKey, value: boolean) =>
        dispatch(setAutoActionPreference({ key, value }));

    const autoActionRow = (
        actionKey: BooleanAutoActionKey,
        icon: ReactNode,
        label: string,
    ) => {
        const enabled = preferences[actionKey];
        return (
            <ListItemButton
                key={actionKey}
                onClick={() => setPreference(actionKey, !enabled)}
                dense
            >
                <ListItemIcon sx={{ minWidth: 36 }}>{icon}</ListItemIcon>
                <ListItemText primary={label} />
                {enabled ? (
                    <Check sx={{ fontSize: 16, color: "success.main" }} />
                ) : (
                    <Close
                        sx={{ fontSize: 16, color: "error.main", opacity: 0.5 }}
                    />
                )}
            </ListItemButton>
        );
    };

    const filteredTags = useMemo(
        () =>
            filterText
                ? tags.filter((tag) =>
                      tag.toLowerCase().includes(filterText.toLowerCase()),
                  )
                : tags,
        [tags, filterText],
    );

    const renderPanelContent = () => {
        switch (activePanel) {
            case LeftSidebarPanel.FOLDER:
                return <FolderView filter={filterText} />;
            case LeftSidebarPanel.TAGS:
                return (
                    <div className={styles.tagListContainer}>
                        <TagsList tags={filteredTags} />
                    </div>
                );
            case LeftSidebarPanel.QUERIES:
                return (
                    <CustomQueriesList
                        hideHeader
                        filter={filterText}
                        highlightedQueryId={highlightedQueryId}
                    />
                );
            case LeftSidebarPanel.BULK_ACTIONS:
                return (
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
                );
            case LeftSidebarPanel.AUTO_ACTIONS:
                return (
                    <List dense disablePadding>
                        {autoActionRow(
                            "flag",
                            <FlagOutlined />,
                            t("sideMenu.autoActions.flag"),
                        )}
                        {autoActionRow(
                            "markAsSeen",
                            <MarkEmailUnreadOutlined />,
                            t("sideMenu.autoActions.markAsSeen"),
                        )}
                        {autoActionRow(
                            "translate",
                            <Translate />,
                            t("sideMenu.autoActions.translate"),
                        )}
                        {autoActionRow(
                            "summarize",
                            <SummarizeOutlined />,
                            t("sideMenu.autoActions.summarize"),
                        )}
                        {autoActionRow(
                            "describeImage",
                            <ImageSearch />,
                            t("sideMenu.autoActions.describeImage"),
                        )}
                        {autoActionRow(
                            "reindex",
                            <YoutubeSearchedForOutlined />,
                            t("sideMenu.autoActions.reindex"),
                        )}
                    </List>
                );
            default:
                return null;
        }
    };

    const sidebarWidth = activePanel === null ? 0 : width;
    const showFilter =
        activePanel !== null && FILTERABLE_PANELS.has(activePanel);

    return (
        <div
            className={`${styles.leftSidebar} ${isDragging ? styles.dragging : ""}`}
            style={{ width: sidebarWidth }}
        >
            {activePanel !== null && (
                <>
                    <div className={styles.header}>
                        <Typography className={styles.headerTitle}>
                            {t(PANEL_TITLES[activePanel])}
                        </Typography>
                        <IconButton
                            size="small"
                            onClick={() => dispatch(setLeftSidebarPanel(null))}
                        >
                            <Close fontSize="small" />
                        </IconButton>
                    </div>
                    {showFilter && (
                        <div className={styles.filterBar}>
                            <InputBase
                                className={styles.filterInput}
                                value={filterText}
                                onChange={(e) => setFilterText(e.target.value)}
                                placeholder="Filter..."
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
                                    filterText ? (
                                        <InputAdornment position="end">
                                            <IconButton
                                                size="small"
                                                onClick={() =>
                                                    setFilterText("")
                                                }
                                                edge="end"
                                            >
                                                <Close
                                                    fontSize="small"
                                                    className={
                                                        styles.filterIcon
                                                    }
                                                />
                                            </IconButton>
                                        </InputAdornment>
                                    ) : null
                                }
                            />
                        </div>
                    )}
                    <div className={styles.content}>{renderPanelContent()}</div>
                    <div
                        className={`${styles.dragHandle} ${isDragging ? styles.dragging : ""}`}
                        onMouseDown={handleMouseDown}
                    />
                </>
            )}
        </div>
    );
};
