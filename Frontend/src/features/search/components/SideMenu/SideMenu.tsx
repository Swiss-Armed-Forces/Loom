import {
    Check,
    ChevronLeft,
    ChevronRight,
    Close,
    ExpandMore,
    FlagOutlined,
    ImageSearch,
    MarkEmailUnreadOutlined,
    SummarizeOutlined,
    Translate,
    YoutubeSearchedForOutlined,
} from "@mui/icons-material";
import {
    Accordion,
    AccordionDetails,
    AccordionSummary,
    Badge,
    Box,
    List,
    ListItem,
    IconButton,
    Tooltip,
    Typography,
} from "@mui/material";
import { ReactNode, useState } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    selectTotalFiles,
    selectQuery,
    selectTags,
    selectSideMenu,
    selectAutoActionsPreferences,
    setAutoActionPreference,
    toggleSideMenu,
    toggleSideMenuAutoActions,
    toggleSideMenuBulkActions,
    toggleSideMenuTags,
    toggleSideMenuQueries,
} from "@app/slices/searchSlice";
import { TagsList } from "@features/search/components";
import {
    ReIndexButton,
    SummaryButton,
    TranslationButton,
    AddTagsButton,
    UpdateFlaggedButton,
    UpdateHiddenButton,
    UpdateSeenButton,
    UploadFileButton,
    CreateArchiveButton,
} from "@features/search/components/FileActionButtons";
import { ImageDescriptionButton } from "@features/search/components/FileActionButtons";

import { CustomQueriesList } from "../CustomQueries/CustomQueries";

import styles from "./SideMenu.module.css";

const accordionSx = {
    background: "transparent",
    "&:before": { display: "none" },
};

const accordionSummarySx = {
    minHeight: 0,
    px: 2,
    py: 0.5,
    transition: "opacity 0.2s ease",
    "&:hover": { opacity: 0.7 },
};

const accordionTitleSx = {
    fontWeight: "medium",
    lineHeight: 1,
};

export const SideMenu = () => {
    const dispatch = useAppDispatch();
    const numberOfResults = useAppSelector(selectTotalFiles);
    const searchQuery = useAppSelector(selectQuery);
    const tags = useAppSelector(selectTags);
    const {
        isExpanded: isMenuExpanded,
        isBulkActionsExpanded,
        isTagsExpanded,
        isQueriesExpanded,
        isAutoActionsExpanded,
    } = useAppSelector(selectSideMenu);
    const [isMenuAnimationRunning, setIsMenuAnimationRunning] = useState(false);
    const preferences = useAppSelector(selectAutoActionsPreferences);
    const setPreference = (key: BooleanAutoActionKey, value: boolean) =>
        dispatch(setAutoActionPreference({ key, value }));

    const { t } = useTranslation();

    const handleToggleSideMenu = () => {
        // Run animation
        setIsMenuAnimationRunning(true);
        // Because .sideMenuContainer CSS class uses 0.2s ease-in-out
        setTimeout(() => {
            dispatch(toggleSideMenu());
            // Animation finished
            setIsMenuAnimationRunning(false);
        }, 230);
    };

    const bulkActionButtons = (
        <>
            <UpdateFlaggedButton iconOnly disabled={numberOfResults === 0} />
            <UpdateSeenButton iconOnly disabled={numberOfResults === 0} />
            <AddTagsButton iconOnly disabled={numberOfResults === 0} />
            <TranslationButton iconOnly disabled={numberOfResults === 0} />
            <SummaryButton iconOnly disabled={numberOfResults === 0} />
            <ImageDescriptionButton iconOnly disabled={numberOfResults === 0} />
            <ReIndexButton iconOnly disabled={numberOfResults === 0} />
            <UpdateHiddenButton iconOnly disabled={numberOfResults === 0} />
            <CreateArchiveButton
                searchQuery={searchQuery}
                iconOnly
                disabled={numberOfResults === 0}
            />
        </>
    );

    type BooleanAutoActionKey =
        | "markAsSeen"
        | "flag"
        | "reindex"
        | "translate"
        | "summarize"
        | "describeImage";

    const autoActionIconButton = (
        actionKey: BooleanAutoActionKey,
        icon: ReactNode,
        label: string,
    ) => {
        const enabled = preferences[actionKey];
        return (
            <Tooltip key={actionKey} title={label}>
                <IconButton
                    size="small"
                    onClick={() => setPreference(actionKey, !enabled)}
                    sx={{
                        transition: "opacity 0.2s ease",
                        "&:hover": { opacity: 0.8 },
                    }}
                >
                    <Badge
                        overlap="circular"
                        anchorOrigin={{
                            vertical: "bottom",
                            horizontal: "right",
                        }}
                        badgeContent={
                            enabled ? (
                                <Check sx={{ fontSize: 10 }} />
                            ) : (
                                <Close sx={{ fontSize: 10 }} />
                            )
                        }
                        color={enabled ? "success" : "error"}
                    >
                        {icon}
                    </Badge>
                </IconButton>
            </Tooltip>
        );
    };

    const autoActionButtons = (
        <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
            {autoActionIconButton(
                "flag",
                <FlagOutlined />,
                t("sideMenu.autoActions.flag"),
            )}
            {autoActionIconButton(
                "markAsSeen",
                <MarkEmailUnreadOutlined />,
                t("sideMenu.autoActions.markAsSeen"),
            )}
            {autoActionIconButton(
                "translate",
                <Translate />,
                t("sideMenu.autoActions.translate"),
            )}
            {autoActionIconButton(
                "summarize",
                <SummarizeOutlined />,
                t("sideMenu.autoActions.summarize"),
            )}
            {autoActionIconButton(
                "describeImage",
                <ImageSearch />,
                t("sideMenu.autoActions.describeImage"),
            )}
            {autoActionIconButton(
                "reindex",
                <YoutubeSearchedForOutlined />,
                t("sideMenu.autoActions.reindex"),
            )}
        </Box>
    );

    return (
        <div
            className={`${styles.sideMenuContainer} ${isMenuAnimationRunning || isMenuExpanded ? styles.open : styles.closed}`}
        >
            <div
                className={`${styles.sideMenu} ${!isMenuExpanded && styles.sideMenuCentered}`}
            >
                <List className={styles.sideMenuActions}>
                    <ListItem>
                        <IconButton
                            onClick={handleToggleSideMenu}
                            size="large"
                            title="Expand/Collapse Menu"
                            sx={{
                                transition:
                                    "transform 0.2s ease, opacity 0.2s ease",
                                "&:hover": {
                                    transform: "scale(1.1)",
                                    opacity: 0.8,
                                },
                            }}
                        >
                            {isMenuExpanded ? (
                                <ChevronLeft />
                            ) : (
                                <ChevronRight />
                            )}
                        </IconButton>
                    </ListItem>
                    <ListItem
                        sx={!isMenuExpanded ? { justifyContent: "center" } : {}}
                    >
                        <UploadFileButton iconOnly={!isMenuExpanded} />
                    </ListItem>
                </List>

                {isMenuExpanded ? (
                    <Accordion
                        expanded={isBulkActionsExpanded}
                        onChange={() => dispatch(toggleSideMenuBulkActions())}
                        disableGutters
                        elevation={0}
                        sx={accordionSx}
                    >
                        <AccordionSummary
                            expandIcon={<ExpandMore />}
                            sx={accordionSummarySx}
                        >
                            <Typography variant="body2" sx={accordionTitleSx}>
                                {t("sideMenu.bulkActions")}
                            </Typography>
                        </AccordionSummary>
                        <AccordionDetails
                            className={styles.bulkActionButtons}
                            sx={{
                                display: "flex",
                                flexWrap: "wrap",
                                gap: 0.5,
                                px: 1,
                                py: 0.5,
                            }}
                        >
                            {bulkActionButtons}
                        </AccordionDetails>
                    </Accordion>
                ) : (
                    isBulkActionsExpanded && (
                        <List>
                            <ListItem
                                className={styles.bulkActionButtons}
                                sx={{
                                    flexWrap: "wrap",
                                    gap: 0.5,
                                    px: 0.5,
                                    justifyContent: "center",
                                }}
                            >
                                {bulkActionButtons}
                            </ListItem>
                        </List>
                    )
                )}

                {isMenuExpanded ? (
                    <Accordion
                        expanded={isAutoActionsExpanded}
                        onChange={() => dispatch(toggleSideMenuAutoActions())}
                        disableGutters
                        elevation={0}
                        sx={accordionSx}
                    >
                        <AccordionSummary
                            expandIcon={<ExpandMore />}
                            sx={accordionSummarySx}
                        >
                            <Typography variant="body2" sx={accordionTitleSx}>
                                {t("sideMenu.autoActions.title")}
                            </Typography>
                        </AccordionSummary>
                        <AccordionDetails sx={{ px: 1, py: 0.5 }}>
                            {autoActionButtons}
                        </AccordionDetails>
                    </Accordion>
                ) : (
                    isAutoActionsExpanded && (
                        <List>
                            <ListItem
                                sx={{
                                    flexWrap: "wrap",
                                    gap: 0.5,
                                    px: 0.5,
                                    justifyContent: "center",
                                }}
                            >
                                {autoActionButtons}
                            </ListItem>
                        </List>
                    )
                )}

                {isMenuExpanded ? (
                    <Accordion
                        expanded={isTagsExpanded}
                        onChange={() => dispatch(toggleSideMenuTags())}
                        disableGutters
                        elevation={0}
                        sx={accordionSx}
                    >
                        <AccordionSummary
                            expandIcon={<ExpandMore />}
                            sx={accordionSummarySx}
                        >
                            <Typography variant="body2" sx={accordionTitleSx}>
                                {t("sideMenu.tags")}
                            </Typography>
                        </AccordionSummary>
                        <AccordionDetails sx={{ p: 0 }}>
                            <div className={styles.tagListContainer}>
                                <TagsList tags={tags} />
                            </div>
                        </AccordionDetails>
                    </Accordion>
                ) : (
                    isTagsExpanded && (
                        <div
                            className={styles.tagListContainer}
                            style={{
                                justifyContent: "center",
                                padding: "4px 8px",
                            }}
                        >
                            <TagsList iconOnly tags={tags} />
                        </div>
                    )
                )}

                {isMenuExpanded ? (
                    <Accordion
                        expanded={isQueriesExpanded}
                        onChange={() => dispatch(toggleSideMenuQueries())}
                        disableGutters
                        elevation={0}
                        sx={accordionSx}
                    >
                        <AccordionSummary
                            expandIcon={<ExpandMore />}
                            sx={accordionSummarySx}
                        >
                            <Typography variant="body2" sx={accordionTitleSx}>
                                {t("sideMenu.savedQueries.title")}
                            </Typography>
                        </AccordionSummary>
                        <AccordionDetails sx={{ p: 0 }}>
                            <CustomQueriesList hideHeader />
                        </AccordionDetails>
                    </Accordion>
                ) : (
                    isQueriesExpanded && (
                        <CustomQueriesList hideHeader iconOnly />
                    )
                )}
            </div>
        </div>
    );
};
