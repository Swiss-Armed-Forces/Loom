import { Delete, ChevronLeft, ChevronRight } from "@mui/icons-material";
import {
    List,
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    ListSubheader,
    IconButton,
    useMediaQuery,
    Switch,
    FormControlLabel,
} from "@mui/material";
import { useState } from "react";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    updateQuery,
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
import { ImageDescriptionButton } from "@features/search/components/FileActionButtons";

import { CustomQueriesList } from "../CustomQueries/CustomQueries";

import styles from "./SideMenu.module.css";

const expertModeKey = "loomExpertMode";

export const SideMenu = () => {
    const numberOfResults = useAppSelector(selectTotalFiles);
    const searchQuery = useAppSelector(selectQuery);
    const tags = useAppSelector(selectTags);
    const [isMenuExpanded, setIsMenuExpanded] = useState(true);
    const [isMenuAnimationRunning, setIsMenuAnimationRunning] = useState(true);
    const [expertMode, setExpertMode] = useState(
        () => window.localStorage.getItem(expertModeKey) === "true",
    );

    const dispatch = useAppDispatch();
    const matchMedia = useMediaQuery("(min-width: 1200px)");
    const { t } = useTranslation();

    const handleShowHiddenFiles = () => {
        dispatch(updateQuery({ query: "hidden:true" }));
    };

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

    useEffect(() => {
        setIsMenuExpanded(matchMedia);
        setIsMenuAnimationRunning(matchMedia);
    }, [matchMedia]);

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
                        >
                            {isMenuExpanded ? (
                                <ChevronLeft />
                            ) : (
                                <ChevronRight />
                            )}
                        </IconButton>
                    </ListItem>
                    <ListItem>
                        <UploadFileButton iconOnly={!isMenuExpanded} />
                    </ListItem>
                    {isMenuExpanded && (
                        <ListItem>
                            <FormControlLabel
                                control={
                                    <Switch
                                        sx={{
                                            ".MuiSwitch-switchBase": {
                                                padding: "9px",
                                            },
                                        }}
                                        checked={expertMode}
                                        onChange={(e) => {
                                            setExpertMode(e.target.checked);
                                            window.localStorage.setItem(
                                                expertModeKey,
                                                e.target.checked.toString(),
                                            );
                                        }}
                                    />
                                }
                                label={t("sideMenu.expertMode")}
                            />
                        </ListItem>
                    )}
                    {expertMode && (
                        <>
                            <ListItem>
                                <AddTagsButton
                                    iconOnly={!isMenuExpanded}
                                    disabled={numberOfResults === 0}
                                />
                            </ListItem>
                            <ListItem>
                                <UpdateSeenButton
                                    iconOnly={!isMenuExpanded}
                                    buttonFullWidth
                                    disabled={numberOfResults === 0}
                                />
                            </ListItem>
                            <ListItem>
                                <UpdateHiddenButton
                                    iconOnly={!isMenuExpanded}
                                    buttonFullWidth
                                    disabled={numberOfResults === 0}
                                />
                            </ListItem>
                            <ListItem>
                                <UpdateFlaggedButton
                                    iconOnly={!isMenuExpanded}
                                    buttonFullWidth
                                    disabled={numberOfResults === 0}
                                />
                            </ListItem>
                            <ListItem>
                                <CreateArchiveButton
                                    searchQuery={searchQuery}
                                    iconOnly={!isMenuExpanded}
                                    disabled={numberOfResults === 0}
                                />
                            </ListItem>
                            <ListItem>
                                <TranslationButton
                                    iconOnly={!isMenuExpanded}
                                    disabled={numberOfResults === 0}
                                />
                            </ListItem>
                            <ListItem>
                                <ReIndexButton
                                    iconOnly={!isMenuExpanded}
                                    disabled={numberOfResults === 0}
                                />
                            </ListItem>
                            <ListItem>
                                <SummaryButton
                                    iconOnly={!isMenuExpanded}
                                    disabled={numberOfResults === 0}
                                />
                            </ListItem>
                            <ListItem>
                                <ImageDescriptionButton
                                    iconOnly={!isMenuExpanded}
                                    disabled={numberOfResults === 0}
                                />
                            </ListItem>
                        </>
                    )}
                </List>
                <List
                    subheader={
                        isMenuExpanded ? (
                            <ListSubheader component="div">
                                {t("sideMenu.tags")}
                            </ListSubheader>
                        ) : (
                            <ListSubheader component="div">
                                <hr />
                            </ListSubheader>
                        )
                    }
                >
                    <div className={styles.tagListContainer}>
                        <TagsList iconOnly={!isMenuExpanded} tags={tags} />
                    </div>
                </List>
                <List
                    subheader={
                        isMenuExpanded ? (
                            <ListSubheader component="div">
                                {t("sideMenu.savedQueries.title")}
                            </ListSubheader>
                        ) : (
                            <ListSubheader component="div">
                                <hr />
                            </ListSubheader>
                        )
                    }
                >
                    <ListItemButton onClick={handleShowHiddenFiles}>
                        <ListItemIcon title={t("sideMenu.hiddenFiles")}>
                            <Delete />
                        </ListItemIcon>
                        {isMenuExpanded ? (
                            <ListItemText primary={t("sideMenu.hiddenFiles")} />
                        ) : (
                            <></>
                        )}
                    </ListItemButton>
                </List>
                <CustomQueriesList iconOnly={!isMenuExpanded} />
            </div>
        </div>
    );
};
