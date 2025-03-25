import {
    List,
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    ListSubheader,
} from "@mui/material";
import { FC, useState } from "react";
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
    setQuery,
    selectCustomQueries,
} from "../../searchSlice.ts";
import { Delete, Policy } from "@mui/icons-material";
import { ConfirmDialog } from "../ConfirmDialog.tsx";

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
    return (
        <>
            {icon_only ? (
                <ListItemButton
                    onClick={() => {
                        dispatch(setQuery(customQuery.query));
                    }}
                    title={customQuery.name}
                >
                    <ListItemIcon>
                        {availableCustomQueryIcons.find(
                            (ac) => ac.key == customQuery.icon,
                        )?.icon ?? <Policy key="Policy" />}
                    </ListItemIcon>
                </ListItemButton>
            ) : (
                <ListItemButton
                    onClick={() => {
                        dispatch(setQuery(customQuery.query));
                    }}
                >
                    <ListItemIcon>
                        {availableCustomQueryIcons.find(
                            (ac) => ac.key == customQuery.icon,
                        )?.icon ?? <Policy key="Policy" />}
                    </ListItemIcon>
                    <ListItemText>{customQuery.name}</ListItemText>
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
