import {
    Badge,
    Chip,
    List,
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    ListSubheader,
} from "@mui/material";
import { FC, useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import styles from "./CustomQueries.module.css";
import {
    AddCustomQueryDialog,
    availableCustomQueryIcons,
} from "./AddCustomQueryDialog.tsx";
import { useAppDispatch, useAppSelector } from "../../../../app/hooks.ts";
import {
    CustomQuery,
    deleteCustomQuery,
    updateQuery,
    selectCustomQueries,
    fetchFilesCountForCustomQuery,
    markCustomQueryAsRead,
} from "../../searchSlice.ts";
import { Delete, Policy } from "@mui/icons-material";
import { ConfirmDialog } from "../ConfirmDialog.tsx";

const CUSTOM_QUERY_FILES_COUNT_POLL_INTERVAL__MS = 30_000;

interface SavedQueryItemProps {
    customQuery: CustomQuery;
    icon_only?: boolean;
}

const CustomQueryItem: FC<SavedQueryItemProps> = ({
    customQuery,
    icon_only = false,
}) => {
    const dispatch = useAppDispatch();
    const [openConfirmDialog, setOpenConfirmDialog] = useState<boolean>(false);
    const { t } = useTranslation();

    const handleConfirmation = async () => {
        dispatch(deleteCustomQuery(customQuery));
        setOpenConfirmDialog(false);
    };

    const onCustomQueryClick = useCallback(() => {
        dispatch(markCustomQueryAsRead(customQuery));
        dispatch(updateQuery(customQuery.query));
    }, [dispatch, customQuery]);

    useEffect(() => {
        const customQueryFilesCountInterval = setInterval(async () => {
            await dispatch(fetchFilesCountForCustomQuery({ customQuery }));
        }, CUSTOM_QUERY_FILES_COUNT_POLL_INTERVAL__MS);

        return () => {
            clearInterval(customQueryFilesCountInterval);
        };
    }, [customQuery, dispatch]);

    return (
        <>
            {icon_only ? (
                <ListItemButton
                    onClick={onCustomQueryClick}
                    title={customQuery.name}
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
                </ListItemButton>
            ) : (
                <ListItemButton onClick={onCustomQueryClick}>
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
                    <ListItemText className={styles.listItemText}>
                        {customQuery.name}{" "}
                        <Chip
                            label={customQuery.fileCount.toString()}
                            size="small"
                        ></Chip>
                    </ListItemText>
                    <ListItemIcon
                        onClick={(e) => {
                            setOpenConfirmDialog(true);
                            e.stopPropagation();
                        }}
                    >
                        <Delete color="error" />
                    </ListItemIcon>
                </ListItemButton>
            )}

            <ConfirmDialog
                open={openConfirmDialog}
                text={t("confirmDialog.confirmCustomQueryRemoval")}
                buttonText={t("confirmDialog.confirmRemoval")}
                handleConfirmation={handleConfirmation}
                cancel={() => setOpenConfirmDialog(false)}
                icon={<Delete />}
            ></ConfirmDialog>
        </>
    );
};

interface CustomQueriesListProps {
    icon_only?: boolean;
}

export const CustomQueriesList: FC<CustomQueriesListProps> = ({
    icon_only = false,
}: CustomQueriesListProps) => {
    const { t } = useTranslation();
    const customQueries = useAppSelector(selectCustomQueries);

    return (
        <List className={styles.savedQueries}>
            {icon_only ? (
                <ListSubheader>
                    <hr />
                </ListSubheader>
            ) : (
                <ListSubheader>
                    {t("sideMenu.savedQueries.title")}
                </ListSubheader>
            )}
            {customQueries.map((q, i) => (
                <CustomQueryItem
                    key={i}
                    customQuery={q}
                    icon_only={icon_only}
                ></CustomQueryItem>
            ))}
            <ListItem>
                <AddCustomQueryDialog icon_only={icon_only} />
            </ListItem>
        </List>
    );
};
