import {
    BarChart,
    Bookmark,
    Forum,
    Folder,
    Label,
    MoreHoriz,
    PlaylistAddCheck,
    Policy,
    Tune,
} from "@mui/icons-material";
import { Badge, Divider, IconButton, Tooltip } from "@mui/material";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    LeftSidebarPanel,
    RightSidebarTab,
    markCustomQueryAsRead,
    selectCustomQueries,
    selectLeftSidebarPanel,
    selectRightSidebarOpen,
    selectRightSidebarTab,
    setHighlightedQueryId,
    setLeftSidebarPanel,
    setRightSidebarTab,
    toggleRightSidebar,
    updateQuery,
} from "@app/slices/searchSlice";
import { UploadFileButton } from "@features/search/components/FileActionButtons";

import { availableCustomQueryIcons } from "../CustomQueries/AddCustomQueryDialog";

import styles from "./ActivityBar.module.css";

export const ActivityBar = () => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();
    const activePanel = useAppSelector(selectLeftSidebarPanel);
    const rightSidebarOpen = useAppSelector(selectRightSidebarOpen);
    const rightSidebarTab = useAppSelector(selectRightSidebarTab);
    const customQueries = useAppSelector(selectCustomQueries);

    const MAX_NEW_MATCH_QUERIES = 5;
    const newMatchQueries = customQueries.filter((q) => q.hasNewFiles);
    const visibleNewMatchQueries = newMatchQueries.slice(
        0,
        MAX_NEW_MATCH_QUERIES,
    );
    const hiddenNewMatchCount =
        newMatchQueries.length - visibleNewMatchQueries.length;

    const handleLeftClick = (panel: LeftSidebarPanel) => {
        dispatch(setLeftSidebarPanel(activePanel === panel ? null : panel));
    };

    const handleRightClick = (tab: RightSidebarTab) => {
        if (rightSidebarOpen && rightSidebarTab === tab) {
            dispatch(toggleRightSidebar());
        } else {
            dispatch(setRightSidebarTab(tab));
        }
    };

    const leftPanelButtons: Array<{
        panel: LeftSidebarPanel;
        icon: React.ReactNode;
        label: string;
    }> = [
        {
            panel: LeftSidebarPanel.FOLDER,
            icon: <Folder />,
            label: t("toolbar.views.folder"),
        },
        {
            panel: LeftSidebarPanel.TAGS,
            icon: <Label />,
            label: t("sideMenu.tags"),
        },
        {
            panel: LeftSidebarPanel.QUERIES,
            icon: <Bookmark />,
            label: t("sideMenu.savedQueries.title"),
        },
        {
            panel: LeftSidebarPanel.BULK_ACTIONS,
            icon: <PlaylistAddCheck />,
            label: t("sideMenu.bulkActions"),
        },
        {
            panel: LeftSidebarPanel.AUTO_ACTIONS,
            icon: <Tune />,
            label: t("sideMenu.autoActions.title"),
        },
    ];

    const rightPanelButtons: Array<{
        tab: RightSidebarTab;
        icon: React.ReactNode;
        label: string;
    }> = [
        {
            tab: RightSidebarTab.STATISTICS,
            icon: <BarChart />,
            label: t("toolbar.views.statistics"),
        },
        {
            tab: RightSidebarTab.CHAT,
            icon: <Forum />,
            label: "Chatbot",
        },
    ];

    return (
        <div className={styles.activityBar}>
            <div className={styles.topSection}>
                <Tooltip
                    title={t("uploadFileDialog.uploadButton")}
                    placement="right"
                >
                    <span>
                        <UploadFileButton iconOnly />
                    </span>
                </Tooltip>
                {leftPanelButtons.map(({ panel, icon, label }) => (
                    <Tooltip key={panel} title={label} placement="right">
                        <IconButton
                            className={`${styles.iconButton} ${activePanel === panel ? styles.active : ""}`}
                            onClick={() => handleLeftClick(panel)}
                            size="medium"
                            color={
                                activePanel === panel ? "primary" : "default"
                            }
                        >
                            {icon}
                        </IconButton>
                    </Tooltip>
                ))}
            </div>
            <div className={styles.bottomSection}>
                {visibleNewMatchQueries.map((q) => {
                    const icon = availableCustomQueryIcons.find(
                        (ac) => ac.key === q.icon,
                    )?.icon ?? <Policy />;
                    return (
                        <Tooltip key={q.name} title={q.name} placement="right">
                            <IconButton
                                className={styles.iconButton}
                                size="medium"
                                onClick={() => {
                                    dispatch(markCustomQueryAsRead(q));
                                    dispatch(
                                        updateQuery({
                                            ...q.query,
                                            id: undefined,
                                        }),
                                    );
                                    dispatch(
                                        setLeftSidebarPanel(
                                            LeftSidebarPanel.QUERIES,
                                        ),
                                    );
                                    dispatch(setHighlightedQueryId(q.id));
                                }}
                            >
                                <Badge color="primary" variant="dot">
                                    {icon}
                                </Badge>
                            </IconButton>
                        </Tooltip>
                    );
                })}
                {hiddenNewMatchCount > 0 && (
                    <Tooltip
                        title={`${hiddenNewMatchCount} more new matches`}
                        placement="right"
                    >
                        <IconButton
                            className={styles.iconButton}
                            size="medium"
                            disabled
                        >
                            <MoreHoriz />
                        </IconButton>
                    </Tooltip>
                )}
                {newMatchQueries.length > 0 && (
                    <Divider
                        flexItem
                        sx={{ width: "60%", alignSelf: "center", my: 0.5 }}
                    />
                )}
                {rightPanelButtons.map(({ tab, icon, label }) => (
                    <Tooltip key={tab} title={label} placement="right">
                        <IconButton
                            className={`${styles.iconButton} ${rightSidebarOpen && rightSidebarTab === tab ? styles.active : ""}`}
                            onClick={() => handleRightClick(tab)}
                            size="medium"
                            color={
                                rightSidebarOpen && rightSidebarTab === tab
                                    ? "primary"
                                    : "default"
                            }
                        >
                            {icon}
                        </IconButton>
                    </Tooltip>
                ))}
            </div>
        </div>
    );
};
