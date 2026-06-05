import { Delete, Policy } from "@mui/icons-material";
import {
    Badge,
    List,
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    ListSubheader,
    Tooltip,
} from "@mui/material";
import { useCallback, useEffect } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks.ts";
import { openDialog } from "@app/slices/commonSlice";
import {
    CustomQuery,
    updateQuery,
    selectCustomQueries,
    selectQuery,
    fetchFilesCountForCustomQuery,
    markCustomQueryAsRead,
} from "@app/slices/searchSlice";
import { DialogType } from "@features/common/utils/enums";

import {
    AddCustomQueryDialog,
    availableCustomQueryIcons,
} from "./AddCustomQueryDialog";
import styles from "./CustomQueries.module.css";

const CUSTOM_QUERY_FILES_COUNT_POLL_INTERVAL_MS = 30_000;

interface SavedQueryItemProps {
    customQuery: CustomQuery;
    iconOnly?: boolean;
}

const CustomQueryItem = ({
    customQuery,
    iconOnly = false,
}: SavedQueryItemProps) => {
    const dispatch = useAppDispatch();

    const handleClick = useCallback(() => {
        dispatch(markCustomQueryAsRead(customQuery));
        dispatch(
            updateQuery({
                ...customQuery.query,
                id: undefined,
            }),
        );
    }, [dispatch, customQuery]);

    const handleDeleteClick = useCallback(
        (e: React.MouseEvent) => {
            e.stopPropagation();
            dispatch(
                openDialog({
                    id: "",
                    type: DialogType.DeleteCustomQuery,
                    props: { customQuery },
                }),
            );
        },
        [dispatch, customQuery],
    );

    useEffect(() => {
        const customQueryFilesCountInterval = setInterval(async () => {
            await dispatch(fetchFilesCountForCustomQuery({ customQuery }));
        }, CUSTOM_QUERY_FILES_COUNT_POLL_INTERVAL_MS);

        return () => {
            clearInterval(customQueryFilesCountInterval);
        };
    }, [customQuery]); // eslint-disable-line react-hooks/exhaustive-deps

    if (iconOnly) {
        return (
            <Tooltip
                title={customQuery.name}
                placement="right"
                enterDelay={200}
            >
                <ListItemButton
                    onClick={handleClick}
                    sx={{
                        transition: "opacity 0.2s ease",
                        "&:hover": { opacity: 0.7 },
                        justifyContent: "center",
                    }}
                >
                    <Badge
                        badgeContent={customQuery.fileCount}
                        color="primary"
                        showZero
                        anchorOrigin={{
                            vertical: "bottom",
                            horizontal: "right",
                        }}
                    >
                        <Badge
                            invisible={!customQuery.hasNewFiles}
                            color="primary"
                            anchorOrigin={{
                                vertical: "top",
                                horizontal: "left",
                            }}
                            variant="dot"
                        >
                            <ListItemIcon>
                                {availableCustomQueryIcons.find(
                                    (ac) => ac.key == customQuery.icon,
                                )?.icon ?? <Policy key="Policy" />}
                            </ListItemIcon>
                        </Badge>
                    </Badge>
                </ListItemButton>
            </Tooltip>
        );
    }

    return (
        <ListItemButton
            onClick={handleClick}
            sx={{
                transition: "opacity 0.2s ease",
                "&:hover": { opacity: 0.7 },
            }}
        >
            <Badge
                badgeContent={customQuery.fileCount}
                color="primary"
                showZero
                anchorOrigin={{
                    vertical: "bottom",
                    horizontal: "right",
                }}
            >
                <Badge
                    invisible={!customQuery.hasNewFiles}
                    color="primary"
                    anchorOrigin={{
                        vertical: "top",
                        horizontal: "left",
                    }}
                    variant="dot"
                >
                    <ListItemIcon>
                        {availableCustomQueryIcons.find(
                            (ac) => ac.key == customQuery.icon,
                        )?.icon ?? <Policy key="Policy" />}
                    </ListItemIcon>
                </Badge>
            </Badge>
            <ListItemText className={styles.listItemText}>
                {customQuery.name}
            </ListItemText>
            <ListItemIcon
                className={styles.deleteIcon}
                onClick={handleDeleteClick}
            >
                <Delete color="error" />
            </ListItemIcon>
        </ListItemButton>
    );
};

interface CustomQueriesListProps {
    iconOnly?: boolean;
    hideHeader?: boolean;
}

export const CustomQueriesList = ({
    iconOnly = false,
    hideHeader = false,
}: CustomQueriesListProps) => {
    const { t } = useTranslation();
    const customQueries = useAppSelector(selectCustomQueries);
    const searchQuery = useAppSelector(selectQuery);

    return (
        <List className={styles.savedQueries}>
            {!hideHeader &&
                (iconOnly ? (
                    <ListSubheader>
                        <hr />
                    </ListSubheader>
                ) : (
                    <ListSubheader>
                        {t("sideMenu.savedQueries.title")}
                    </ListSubheader>
                ))}
            {customQueries.map((q, i) => (
                <CustomQueryItem
                    key={i}
                    customQuery={q}
                    iconOnly={iconOnly}
                ></CustomQueryItem>
            ))}
            <ListItem sx={iconOnly ? { justifyContent: "center" } : {}}>
                <AddCustomQueryDialog
                    iconOnly={iconOnly}
                    disabled={!searchQuery}
                />
            </ListItem>
        </List>
    );
};
