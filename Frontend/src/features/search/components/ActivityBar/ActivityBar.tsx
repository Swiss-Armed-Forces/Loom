import {
    ArticleOutlined,
    BarChartOutlined,
    Bookmark,
    ForumOutlined,
    Folder,
    FolderOpenOutlined,
    Label,
    MoreHoriz,
    PlaylistAddCheckOutlined,
    Policy,
    Tune,
} from "@mui/icons-material";
import {
    Badge,
    Divider,
    IconButton,
    Tooltip,
    useMediaQuery,
} from "@mui/material";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    LeftSidebarPanel,
    RightSidebarTab,
    markCustomQueryAsRead,
    selectCustomQueries,
    selectLeftSidebarPanel,
    closeRightSidebar,
    selectRightSidebarOpen,
    selectRightSidebarTab,
    setHighlightedQueryId,
    setLeftSidebarPanel,
    setRightSidebarTab,
    updateQuery,
} from "@app/slices/searchSlice";
import { getTourLeftPanel, getTourRightTab } from "@app/tours/tourScene";
import { useTour } from "@app/tours/useTour";
import { ActivityBarLayout } from "@features/common/components/ActivityBar/ActivityBarLayout";
import activityBarStyles from "@features/common/components/ActivityBar/ActivityBarLayout.module.css";
import { formatCompactNumber } from "@features/common/utils/helpers";
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
    const isMobile = useMediaQuery("(max-width:600px)");
    const { activeTourStepId, isTourActive } = useTour();
    const tourLeftPanel = getTourLeftPanel(isTourActive, activeTourStepId);
    const tourRightTab = getTourRightTab(isTourActive, activeTourStepId);
    const effectiveLeftPanel =
        tourLeftPanel !== undefined ? tourLeftPanel : activePanel;
    const effectiveRightOpen =
        tourRightTab !== undefined ? tourRightTab !== null : rightSidebarOpen;
    const effectiveRightTab = tourRightTab ?? rightSidebarTab;

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
        if (rightSidebarTab === tab) {
            dispatch(closeRightSidebar());
        } else {
            dispatch(setRightSidebarTab(tab));
        }
    };

    const leftPanelButtons: Array<{
        panel: LeftSidebarPanel;
        icon: React.ReactNode;
        label: string;
        dataTour?: string;
    }> = [
        {
            panel: LeftSidebarPanel.FOLDER,
            icon: <Folder />,
            label: t("toolbar.views.folder"),
            dataTour: "activity-bar-folders",
        },
        {
            panel: LeftSidebarPanel.TAGS,
            icon: <Label />,
            label: t("sideMenu.tags"),
            dataTour: "activity-bar-tags",
        },
        {
            panel: LeftSidebarPanel.QUERIES,
            icon: <Bookmark />,
            label: t("sideMenu.savedQueries.title"),
            dataTour: "activity-bar-saved-queries",
        },
        {
            panel: LeftSidebarPanel.CARD_CUSTOMIZATION,
            icon: <Tune />,
            label: t("sideMenu.cardCustomization.title"),
            dataTour: "sidebar-card-customization",
        },
        {
            panel: LeftSidebarPanel.CHAT,
            icon: <ForumOutlined />,
            label: "AI Assistant",
            dataTour: "sidebar-chat",
        },
    ];

    const rightPanelButtons: Array<{
        tab: RightSidebarTab;
        icon: React.ReactNode;
        label: string;
        dataTour?: string;
    }> = [
        {
            tab: RightSidebarTab.FILE_DETAIL,
            icon: <ArticleOutlined />,
            label: t("toolbar.views.fileDetail"),
            dataTour: "sidebar-file-detail",
        },
        {
            tab: RightSidebarTab.FOLDER,
            icon: <FolderOpenOutlined />,
            label: t("toolbar.views.filteredFolder"),
            dataTour: "sidebar-filtered-folder",
        },
        {
            tab: RightSidebarTab.STATISTICS,
            icon: <BarChartOutlined />,
            label: t("toolbar.views.statistics"),
            dataTour: "sidebar-statistics",
        },
        {
            tab: RightSidebarTab.BULK_ACTIONS,
            icon: <PlaylistAddCheckOutlined />,
            label: t("sideMenu.bulkActions"),
            dataTour: "sidebar-bulk-actions",
        },
    ];

    if (isMobile) {
        return (
            <>
                <div
                    className={styles.activityBarBottom}
                    data-tour="activity-bar"
                >
                    <div
                        className={styles.mobileLeftGroup}
                        data-tour="activity-bar-left"
                    >
                        <Tooltip
                            title={t("uploadFileDialog.uploadButton")}
                            placement="top"
                        >
                            <span data-tour="upload">
                                <UploadFileButton iconOnly />
                            </span>
                        </Tooltip>
                        {leftPanelButtons.map(({ panel, icon, label }) => (
                            <Tooltip key={panel} title={label} placement="top">
                                <IconButton
                                    className={`${styles.iconButtonBottom} ${effectiveLeftPanel === panel ? styles.active : ""}`}
                                    onClick={() => handleLeftClick(panel)}
                                    size="medium"
                                    color={
                                        effectiveLeftPanel === panel
                                            ? "primary"
                                            : "default"
                                    }
                                >
                                    {panel === LeftSidebarPanel.QUERIES &&
                                    newMatchQueries.length > 0 ? (
                                        <Badge
                                            color="primary"
                                            badgeContent={formatCompactNumber(
                                                newMatchQueries.length,
                                            )}
                                        >
                                            {icon}
                                        </Badge>
                                    ) : (
                                        icon
                                    )}
                                </IconButton>
                            </Tooltip>
                        ))}
                    </div>
                    <div
                        className={styles.mobileRightGroup}
                        data-tour="activity-bar-right"
                    >
                        {rightPanelButtons.map(
                            ({ tab, icon, label, dataTour }) => (
                                <Tooltip
                                    key={tab}
                                    title={label}
                                    placement="top"
                                >
                                    <IconButton
                                        className={`${styles.iconButtonBottom} ${effectiveRightOpen && effectiveRightTab === tab ? styles.active : ""}`}
                                        onClick={() => handleRightClick(tab)}
                                        size="medium"
                                        color={
                                            effectiveRightOpen &&
                                            effectiveRightTab === tab
                                                ? "primary"
                                                : "default"
                                        }
                                        {...(dataTour
                                            ? { "data-tour": dataTour }
                                            : {})}
                                    >
                                        {icon}
                                    </IconButton>
                                </Tooltip>
                            ),
                        )}
                    </div>
                </div>
            </>
        );
    }

    const topContent = (
        <>
            <Tooltip
                title={t("uploadFileDialog.uploadButton")}
                placement="right"
            >
                <span data-tour="upload">
                    <UploadFileButton iconOnly />
                </span>
            </Tooltip>
            {leftPanelButtons.map(({ panel, icon, label, dataTour }) => (
                <Tooltip key={panel} title={label} placement="right">
                    <IconButton
                        className={`${activityBarStyles.iconButton} ${effectiveLeftPanel === panel ? activityBarStyles.active : ""}`}
                        onClick={() => handleLeftClick(panel)}
                        size="medium"
                        color={
                            effectiveLeftPanel === panel ? "primary" : "default"
                        }
                        {...(dataTour ? { "data-tour": dataTour } : {})}
                    >
                        {icon}
                    </IconButton>
                </Tooltip>
            ))}
        </>
    );

    const bottomContent = (
        <>
            {visibleNewMatchQueries.map((q) => {
                const icon = availableCustomQueryIcons.find(
                    (ac) => ac.key === q.icon,
                )?.icon ?? <Policy />;
                return (
                    <Tooltip key={q.name} title={q.name} placement="right">
                        <IconButton
                            className={activityBarStyles.iconButton}
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
                        className={activityBarStyles.iconButton}
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
            {rightPanelButtons.map(({ tab, icon, label, dataTour }) => (
                <Tooltip key={tab} title={label} placement="right">
                    <IconButton
                        className={`${activityBarStyles.iconButton} ${effectiveRightOpen && effectiveRightTab === tab ? activityBarStyles.active : ""}`}
                        onClick={() => handleRightClick(tab)}
                        size="medium"
                        color={
                            effectiveRightOpen && effectiveRightTab === tab
                                ? "primary"
                                : "default"
                        }
                        {...(dataTour ? { "data-tour": dataTour } : {})}
                    >
                        {icon}
                    </IconButton>
                </Tooltip>
            ))}
        </>
    );

    return (
        <ActivityBarLayout
            top={topContent}
            bottom={bottomContent}
            dataTour="activity-bar"
            dataTourTop="activity-bar-left"
            dataTourBottom="activity-bar-right"
        />
    );
};
