import { ChevronLeft, ChevronRight, ExpandMore } from "@mui/icons-material";
import {
    Accordion,
    AccordionDetails,
    AccordionSummary,
    List,
    ListItem,
    IconButton,
    Typography,
} from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useAppSelector } from "@app/hooks";
import {
    selectTotalFiles,
    selectQuery,
    selectTags,
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

export const SideMenu = () => {
    const numberOfResults = useAppSelector(selectTotalFiles);
    const searchQuery = useAppSelector(selectQuery);
    const tags = useAppSelector(selectTags);
    const [isMenuExpanded, setIsMenuExpanded] = useState(false);
    const [isMenuAnimationRunning, setIsMenuAnimationRunning] = useState(false);
    const [isBulkActionsExpanded, setIsBulkActionsExpanded] = useState(false);
    const [isTagsExpanded, setIsTagsExpanded] = useState(true);
    const [isQueriesExpanded, setIsQueriesExpanded] = useState(true);

    const { t } = useTranslation();

    const toggleSideMenu = () => {
        // Run animation
        setIsMenuAnimationRunning(true);
        // Because .sideMenuContainer CSS class uses 0.2s ease-in-out
        setTimeout(() => {
            setIsMenuExpanded(!isMenuExpanded);
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
            <ReIndexButton iconOnly disabled={numberOfResults === 0} />
            <UpdateHiddenButton iconOnly disabled={numberOfResults === 0} />
            <CreateArchiveButton
                searchQuery={searchQuery}
                iconOnly
                disabled={numberOfResults === 0}
            />
        </>
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
                            onClick={toggleSideMenu}
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
                        onChange={() => setIsBulkActionsExpanded((v) => !v)}
                        disableGutters
                        elevation={0}
                        sx={accordionSx}
                    >
                        <AccordionSummary
                            expandIcon={<ExpandMore />}
                            sx={accordionSummarySx}
                        >
                            <Typography variant="body2">
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
                        expanded={isTagsExpanded}
                        onChange={() => setIsTagsExpanded((v) => !v)}
                        disableGutters
                        elevation={0}
                        sx={accordionSx}
                    >
                        <AccordionSummary
                            expandIcon={<ExpandMore />}
                            sx={accordionSummarySx}
                        >
                            <Typography variant="body2">
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
                        onChange={() => setIsQueriesExpanded((v) => !v)}
                        disableGutters
                        elevation={0}
                        sx={accordionSx}
                    >
                        <AccordionSummary
                            expandIcon={<ExpandMore />}
                            sx={accordionSummarySx}
                        >
                            <Typography variant="body2">
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
