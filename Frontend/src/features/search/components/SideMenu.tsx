import { useState } from "react";
import {
    ArchiveOutlined,
    Delete,
    ChevronLeft,
    ChevronRight,
} from "@mui/icons-material";
import {
    Button,
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
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";
import { useAppDispatch, useAppSelector } from "../../../app/hooks";
import { setBackgroundTaskSpinnerActive } from "../../common/commonSlice";
import {
    updateQuery,
    selectTotalFiles,
    selectQuery,
    selectTags,
} from "../searchSlice";
import styles from "./SideMenu.module.css";
import { UploadFileDialog } from "./UploadFileDialog";
import { TagsInput } from "../../common/components/tags/TagsInput.tsx";
import { ConfirmDialog } from "./ConfirmDialog";
import { TranslationDialog } from "./TranslationDialog";
import { TagsList } from "../../common/components/tags/TagsList.tsx";
import { CustomQueriesList } from "./CustomQueries/CustomQueries.tsx";
import { ReIndexButton } from "./ReIndexButton.tsx";
import { SummaryButton } from "./SummaryButton.tsx";
import { UpdateVisibilityButton } from "../../common/components/files/UpdateVisibilityStateButton.tsx";
import { scheduleArchiveCreation } from "../../../app/api/search.ts";
import { useEffect } from "react";

const expertModeKey = "loomExpertMode";

export function SideMenu() {
    const numberOfResults = useAppSelector(selectTotalFiles);
    const searchQuery = useAppSelector(selectQuery);
    const tags = useAppSelector(selectTags);
    const [
        openConfirmArchiveCreationDialog,
        setOpenConfirmArchiveCreationDialog,
    ] = useState(false);
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

    const startArchiveCreation = () => {
        if (!searchQuery) return;
        setOpenConfirmArchiveCreationDialog(false);
        scheduleArchiveCreation(searchQuery)
            .then(() => {
                dispatch(setBackgroundTaskSpinnerActive());
                toast.success(
                    "Creation of archive successfully scheduled. Please go to archives.",
                );
            })
            .catch((err) => {
                toast.error(
                    "Cannot schedule archive creation. Code: " +
                        err.status +
                        ", Text: " +
                        err.text,
                );
            });
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
                        <UploadFileDialog icon_only={!isMenuExpanded} />
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
                                <TagsInput
                                    icon_only={!isMenuExpanded}
                                    button_full_width
                                    disabled={numberOfResults === 0}
                                />
                            </ListItem>
                            <ListItem>
                                <UpdateVisibilityButton
                                    icon_only={!isMenuExpanded}
                                    button_full_width
                                    disabled={numberOfResults === 0}
                                />
                            </ListItem>
                            <ListItem>
                                {isMenuExpanded ? (
                                    <Button
                                        onClick={() =>
                                            setOpenConfirmArchiveCreationDialog(
                                                true,
                                            )
                                        }
                                        disabled={numberOfResults === 0}
                                        color="secondary"
                                        variant="contained"
                                        startIcon={<ArchiveOutlined />}
                                        fullWidth={true}
                                    >
                                        <span className="btn-label">
                                            {t("sideMenu.createArchive")}
                                        </span>
                                    </Button>
                                ) : (
                                    <IconButton
                                        onClick={() =>
                                            setOpenConfirmArchiveCreationDialog(
                                                true,
                                            )
                                        }
                                        disabled={numberOfResults === 0}
                                        title={t("sideMenu.createArchive")}
                                    >
                                        <ArchiveOutlined />
                                    </IconButton>
                                )}

                                <ConfirmDialog
                                    open={openConfirmArchiveCreationDialog}
                                    text={t(
                                        "confirmDialog.confirmArchiveCreationText",
                                    )}
                                    buttonText={t(
                                        "confirmDialog.confirmArchiveCreation",
                                    )}
                                    handleConfirmation={startArchiveCreation}
                                    cancel={() =>
                                        setOpenConfirmArchiveCreationDialog(
                                            false,
                                        )
                                    }
                                    icon={<ArchiveOutlined />}
                                />
                            </ListItem>
                            <ListItem>
                                <TranslationDialog
                                    icon_only={!isMenuExpanded}
                                    disabled={numberOfResults === 0}
                                />
                            </ListItem>
                            <ListItem>
                                <ReIndexButton
                                    icon_only={!isMenuExpanded}
                                    disabled={numberOfResults === 0}
                                />
                            </ListItem>
                            <ListItem>
                                <SummaryButton
                                    icon_only={!isMenuExpanded}
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
                        <TagsList icon_only={!isMenuExpanded} tags={tags} />
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
                <CustomQueriesList icon_only={!isMenuExpanded} />
            </div>
        </div>
    );
}
