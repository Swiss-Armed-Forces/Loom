import {
    FlagOutlined,
    ImageSearch,
    MarkEmailUnreadOutlined,
    SummarizeOutlined,
    Translate,
    YoutubeSearchedForOutlined,
} from "@mui/icons-material";
import {
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    Switch,
} from "@mui/material";
import { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    AutoActionsPreferences,
    selectAutoActionsPreferences,
    setAutoActionPreference,
} from "@app/slices/searchSlice";

/** One action and whether it runs. Switched, not ticked: a setting that is
 *  changed in place reads as a switch everywhere else in this panel. */
interface AutoAction {
    key: keyof AutoActionsPreferences;
    icon: ReactNode;
    labelKey: string;
}

const AUTO_ACTIONS: AutoAction[] = [
    {
        key: "flag",
        icon: <FlagOutlined />,
        labelKey: "sideMenu.autoActions.flag",
    },
    {
        key: "markAsSeen",
        icon: <MarkEmailUnreadOutlined />,
        labelKey: "sideMenu.autoActions.markAsSeen",
    },
    {
        key: "translate",
        icon: <Translate />,
        labelKey: "sideMenu.autoActions.translate",
    },
    {
        key: "summarize",
        icon: <SummarizeOutlined />,
        labelKey: "sideMenu.autoActions.summarize",
    },
    {
        key: "describeImage",
        icon: <ImageSearch />,
        labelKey: "sideMenu.autoActions.describeImage",
    },
    {
        key: "reindex",
        icon: <YoutubeSearchedForOutlined />,
        labelKey: "sideMenu.autoActions.reindex",
    },
];

/**
 * What happens to a file when it is opened.
 *
 * Its own tab rather than a third section of the card panel: these settings
 * schedule work on the server, which has nothing to do with how a card is
 * drawn, and the card panel is long enough without them.
 */
export const AutoActionsPanel = () => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();
    const preferences = useAppSelector(selectAutoActionsPreferences);

    return (
        <List dense disablePadding data-tour="customization-auto-actions">
            {AUTO_ACTIONS.map(({ key, icon, labelKey }) => (
                <ListItem
                    key={key}
                    secondaryAction={
                        <Switch
                            edge="end"
                            size="small"
                            checked={preferences[key]}
                            onChange={(e) =>
                                dispatch(
                                    setAutoActionPreference({
                                        key,
                                        value: e.target.checked,
                                    }),
                                )
                            }
                        />
                    }
                >
                    <ListItemIcon sx={{ minWidth: 36 }}>{icon}</ListItemIcon>
                    <ListItemText primary={t(labelKey)} />
                </ListItem>
            ))}
        </List>
    );
};
