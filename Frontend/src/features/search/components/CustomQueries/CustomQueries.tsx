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
import { useCallback, useEffect, useRef } from "react";
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
    highlighted?: boolean;
}

const CustomQueryItem = ({
    customQuery,
    iconOnly = false,
    highlighted = false,
}: SavedQueryItemProps) => {
    const itemRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (highlighted && itemRef.current) {
            itemRef.current.scrollIntoView({
                block: "nearest",
                behavior: "smooth",
            });
        }
    }, [highlighted]);
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
            ref={itemRef}
            selected={highlighted}
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
    filter?: string;
    highlightedQueryId?: string | null;
}

export const CustomQueriesList = ({
    iconOnly = false,
    hideHeader = false,
    filter,
    highlightedQueryId,
}: CustomQueriesListProps) => {
    const { t } = useTranslation();
    const customQueries = useAppSelector(selectCustomQueries);
    const searchQuery = useAppSelector(selectQuery);

    const visibleQueries = filter
        ? customQueries.filter((q) =>
              q.name.toLowerCase().includes(filter.toLowerCase()),
          )
        : customQueries;

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
            {visibleQueries.map((q, i) => (
                <CustomQueryItem
                    key={i}
                    customQuery={q}
                    iconOnly={iconOnly}
                    highlighted={
                        !!highlightedQueryId && q.id === highlightedQueryId
                    }
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
