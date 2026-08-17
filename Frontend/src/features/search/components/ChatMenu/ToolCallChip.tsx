import { Close } from "@mui/icons-material";
import {
    Chip,
    CircularProgress,
    Dialog,
    DialogContent,
    DialogTitle,
    IconButton,
    Typography,
} from "@mui/material";
import { Box } from "@mui/material";
import { useState } from "react";
import AceEditorImport from "react-ace";

import { useDarkMode } from "@features/common/hooks/useDarkMode";

import "ace-builds/esm-resolver";

import type { ToolCallRecord } from "./ChatWindow.types";

const AceEditor = (AceEditorImport as any).default ?? AceEditorImport;

const formatJson = (s: string) => {
    try {
        return JSON.stringify(JSON.parse(s), null, 2);
    } catch {
        return s;
    }
};

export const ToolCallChip = ({ toolCall }: { toolCall: ToolCallRecord }) => {
    const [open, setOpen] = useState(false);
    const isDarkMode = useDarkMode();
    const running = toolCall.status === "running";
    return (
        <>
            <Chip
                label={toolCall.label}
                size="small"
                variant="outlined"
                icon={running ? <CircularProgress size={10} /> : undefined}
                onClick={running ? undefined : () => setOpen(true)}
                sx={{
                    fontSize: "0.7rem",
                    height: 22,
                    cursor: running ? "default" : "pointer",
                    "& .MuiChip-icon": { fontSize: 10 },
                }}
            />
            <Dialog
                open={open}
                onClose={() => setOpen(false)}
                maxWidth="sm"
                fullWidth
            >
                <DialogTitle sx={{ pr: 6 }}>
                    {toolCall.label}
                    <IconButton
                        size="small"
                        onClick={() => setOpen(false)}
                        sx={{ position: "absolute", right: 8, top: 8 }}
                    >
                        <Close fontSize="small" />
                    </IconButton>
                </DialogTitle>
                <DialogContent dividers>
                    <Typography variant="caption" color="text.secondary">
                        Input
                    </Typography>
                    <Box sx={{ mt: 0.5, mb: 2 }}>
                        <AceEditor
                            mode="json"
                            value={formatJson(toolCall.args)}
                            readOnly
                            width="100%"
                            height="200px"
                            theme={isDarkMode ? "tomorrow_night" : "github"}
                            setOptions={{ useWorker: false }}
                            editorProps={{ $blockScrolling: true }}
                        />
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                        Output
                    </Typography>
                    <Box sx={{ mt: 0.5 }}>
                        <AceEditor
                            mode="json"
                            value={formatJson(toolCall.result)}
                            readOnly
                            width="100%"
                            height="200px"
                            theme={isDarkMode ? "tomorrow_night" : "github"}
                            setOptions={{ useWorker: false }}
                            editorProps={{ $blockScrolling: true }}
                        />
                    </Box>
                </DialogContent>
            </Dialog>
        </>
    );
};
