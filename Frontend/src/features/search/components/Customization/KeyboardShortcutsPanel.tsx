import {
    Box,
    Table,
    TableBody,
    TableCell,
    TableRow,
    Typography,
    Button,
} from "@mui/material";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    selectShortcutsBindings,
    resetAllBindings,
} from "@app/slices/searchSlice";
import { KeyRecorder } from "@features/search/components/KeyRecorder/KeyRecorder";
import { shortcutRegistry } from "@features/search/hooks/shortcutRegistry";

export const KeyboardShortcutsPanel = () => {
    const dispatch = useAppDispatch();
    const bindings = useAppSelector(selectShortcutsBindings);
    const { t } = useTranslation();

    // Check if there are any custom bindings
    const hasCustomBindings = Object.keys(bindings).length > 0;

    const handleResetAll = () => {
        dispatch(resetAllBindings());
    };

    return (
        <Box data-tour="card-customization-shortcuts">
            <Box
                sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    pt: 1.5,
                    pb: 0.5,
                }}
            >
                <Typography variant="subtitle2" sx={{ lineHeight: 2.5 }}>
                    {t("emptySearch.hotkeys.title")}
                </Typography>
                {hasCustomBindings && (
                    <Button
                        size="small"
                        variant="outlined"
                        color="secondary"
                        onClick={handleResetAll}
                        sx={{ fontSize: "0.75rem" }}
                    >
                        {t("sideMenu.customizations.resetAll")}
                    </Button>
                )}
            </Box>
            <Table
                size="small"
                sx={{
                    "& td": {
                        fontSize: "0.82rem",
                        border: 0,
                        px: 0,
                        py: 0.25,
                    },
                }}
            >
                <TableBody>
                    {shortcutRegistry
                        .filter(
                            (action) =>
                                action.defaultKeys.length > 0 &&
                                action.id !== "results" &&
                                action.id !== "open" &&
                                action.id !== "openBackground" &&
                                action.id !== "shiftClickNegate" &&
                                action.id !== "ctrlClickAccumulate",
                        )
                        .map((action) => (
                            <TableRow key={action.id}>
                                <TableCell
                                    sx={{
                                        pr: 1.5,
                                        verticalAlign: "top",
                                        py: "0.25rem !important",
                                    }}
                                >
                                    <KeyRecorder
                                        actionId={action.id}
                                        currentKeys={
                                            bindings[action.id] ||
                                            action.defaultKeys
                                        }
                                        defaultKeys={action.defaultKeys}
                                    />
                                </TableCell>
                                <TableCell
                                    sx={{
                                        verticalAlign: "middle",
                                        pt: "6px",
                                    }}
                                >
                                    <Box
                                        sx={{
                                            display: "flex",
                                            alignItems: "center",
                                            gap: 0.5,
                                        }}
                                    >
                                        {action.icon && (
                                            <Box
                                                component="span"
                                                sx={{
                                                    display: "flex",
                                                    color: "text.secondary",
                                                    fontSize: "1rem",
                                                }}
                                            >
                                                {action.icon}
                                            </Box>
                                        )}
                                        <span>
                                            {typeof action.labelKey === "string"
                                                ? t(action.labelKey)
                                                : action.labelKey}
                                        </span>
                                    </Box>
                                </TableCell>
                            </TableRow>
                        ))}
                </TableBody>
            </Table>
        </Box>
    );
};
