import {
    AttachFile,
    Download,
    Flag,
    Fullscreen,
    LabelOutlined,
    ManageSearch,
    MarkEmailReadOutlined,
    Share,
    SubdirectoryArrowLeft,
    SummarizeOutlined,
    Translate,
    YoutubeSearchedForOutlined,
} from "@mui/icons-material";
import { Box } from "@mui/material";
import { t } from "i18next";
import { ReactNode } from "react";

export const formatKey = (key: string): string => {
    const arrowMap: Record<string, string> = {
        ArrowLeft: "←",
        ArrowRight: "→",
        ArrowUp: "↑",
        ArrowDown: "↓",
    };

    // Handle combinations like "Shift + ArrowLeft"
    if (key.includes(" + ")) {
        return key.split(" + ").map(formatKey).join(" + ");
    }

    return arrowMap[key] || key;
};

interface ShortcutAction {
    id: string; // e.g. "moveDown", "download", "toggleSeen"
    defaultKeys: string[]; // e.g. ["j", "ArrowDown"]
    context: "results" | "panel" | "shared";
    icon?: ReactNode; // for display in the defaultKeys tab and empty page
    labelKey: string | ReactNode; // i18n translation key
}

// Registry of default shortcuts

export const shortcutRegistry: ShortcutAction[] = [
    {
        id: "moveDown",
        defaultKeys: ["ArrowDown", "j"],
        labelKey: "emptySearch.hotkeys.moveDown",
        context: "results",
    },
    {
        id: "moveUp",
        defaultKeys: ["ArrowUp", "k"],
        labelKey: "emptySearch.hotkeys.moveUp",
        context: "results",
    },
    {
        id: "prevTab",
        defaultKeys: ["ArrowLeft", "h"],
        labelKey: "emptySearch.hotkeys.prevTab",
        context: "results",
    },
    {
        id: "nextTab",
        defaultKeys: ["ArrowRight", "l"],
        labelKey: "emptySearch.hotkeys.nextTab",
        context: "results",
    },
    {
        id: "prevCenterTab",
        defaultKeys: ["Shift + ArrowLeft", "Shift + h"],
        labelKey: "emptySearch.hotkeys.prevCenterTab",
        context: "results",
    },
    {
        id: "nextCenterTab",
        defaultKeys: ["Shift + ArrowRight", "Shift + l"],
        labelKey: "emptySearch.hotkeys.nextCenterTab",
        context: "results",
    },
    {
        id: "openOrClose",
        defaultKeys: ["i"],
        labelKey: "emptySearch.hotkeys.openOrClose",
        context: "results",
    },
    {
        id: "open",
        defaultKeys: ["Enter", "Double-click"],
        labelKey: "emptySearch.hotkeys.open",
        context: "results",
    },
    {
        id: "openBackground",
        defaultKeys: ["Shift + Enter", "Shift + i", "Ctrl + click"],
        labelKey: t("emptySearch.hotkeys.openBackground"),
        context: "results",
    },
    {
        id: "shiftClickNegate",
        defaultKeys: ["Shift + click"],
        labelKey: (
            <>
                {t("emptySearch.hotkeys.shiftClickNegate")}{" "}
                <Box
                    component="span"
                    sx={{
                        opacity: 0.5,
                        fontSize: "0.9em",
                        whiteSpace: "nowrap",
                    }}
                >
                    (
                    <ManageSearch
                        fontSize="inherit"
                        sx={{ verticalAlign: "middle" }}
                    />{" "}
                    {t("emptySearch.hotkeys.icon")})
                </Box>
            </>
        ),
        context: "results",
    },
    {
        id: "ctrlClickAccumulate",
        defaultKeys: ["Ctrl + click"],
        labelKey: (
            <>
                {t("emptySearch.hotkeys.ctrlClickAccumulate")}{" "}
                <Box
                    component="span"
                    sx={{
                        opacity: 0.5,
                        fontSize: "0.9em",
                        whiteSpace: "nowrap",
                    }}
                >
                    (
                    <ManageSearch
                        fontSize="inherit"
                        sx={{ verticalAlign: "middle" }}
                    />{" "}
                    {t("emptySearch.hotkeys.icon")})
                </Box>
            </>
        ),
        context: "results",
    },
    {
        id: "escapeAction",
        defaultKeys: ["Escape"],
        labelKey: "emptySearch.hotkeys.escapeAction",
        context: "results",
    },
    {
        id: "focusSearch",
        defaultKeys: ["/"],
        labelKey: "emptySearch.hotkeys.focusSearch",
        context: "results",
    },
    {
        id: "results",
        defaultKeys: [],
        context: "results",
        labelKey: "",
    },
    {
        id: "fullscreen",
        defaultKeys: ["f"],
        icon: <Fullscreen fontSize="inherit" />,
        labelKey: "emptySearch.hotkeys.fullscreen",
        context: "results",
    },
    {
        id: "flag",
        defaultKeys: ["Shift + f"],
        icon: <Flag fontSize="inherit" />,
        labelKey: "emptySearch.hotkeys.flag",
        context: "results",
    },
    {
        id: "seen",
        defaultKeys: ["s"],
        icon: <MarkEmailReadOutlined fontSize="inherit" />,
        labelKey: "emptySearch.hotkeys.seen",
        context: "results",
    },
    {
        id: "tag",
        defaultKeys: ["t"],
        icon: <LabelOutlined fontSize="inherit" />,
        labelKey: "emptySearch.hotkeys.tag",
        context: "results",
    },
    {
        id: "navigateParentFile",
        defaultKeys: ["n"],
        icon: (
            <SubdirectoryArrowLeft
                fontSize="inherit"
                sx={{ transform: "rotate(90deg)" }}
            />
        ),
        labelKey: "emptySearch.hotkeys.navigateParentFile",
        context: "results",
    },
    {
        id: "NavigateChildFile",
        defaultKeys: ["Shift + n"],
        icon: <AttachFile fontSize="inherit" />,
        labelKey: "emptySearch.hotkeys.navigateChildFile",
        context: "results",
    },
    {
        id: "copyLink",
        defaultKeys: ["Shift + c"],
        icon: <Share fontSize="inherit" />,
        labelKey: "emptySearch.hotkeys.copyLink",
        context: "results",
    },
    {
        id: "translate",
        defaultKeys: ["Shift + t"],
        icon: <Translate fontSize="inherit" />,
        labelKey: "emptySearch.hotkeys.translate",
        context: "results",
    },
    {
        id: "summarize",
        defaultKeys: ["Shift + s"],
        icon: <SummarizeOutlined fontSize="inherit" />,
        labelKey: "emptySearch.hotkeys.summarize",
        context: "results",
    },
    {
        id: "reindex",
        defaultKeys: ["r"],
        icon: <YoutubeSearchedForOutlined fontSize="inherit" />,
        labelKey: "emptySearch.hotkeys.reindex",
        context: "results",
    },
    {
        id: "download",
        defaultKeys: ["d"],
        icon: <Download fontSize="inherit" />,
        labelKey: "emptySearch.hotkeys.download",
        context: "results",
    },
];
