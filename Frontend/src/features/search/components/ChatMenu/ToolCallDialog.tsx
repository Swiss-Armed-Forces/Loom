import { Close } from "@mui/icons-material";
import {
    Box,
    Dialog,
    DialogContent,
    DialogTitle,
    IconButton,
    Typography,
} from "@mui/material";
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

const TITLE_SX = { pr: 6 } as const;
const CLOSE_SX = { position: "absolute", right: 8, top: 8 } as const;
const INPUT_BOX_SX = { mt: 0.5, mb: 2 } as const;
const OUTPUT_BOX_SX = { mt: 0.5 } as const;

/**
 * The input and output of one tool call.
 *
 * Mounted only while open: `formatJson` re-parses and re-stringifies the whole
 * payload, which for a paged search result is tens of kilobytes, and it would
 * otherwise run on every chip on every render of the thread.
 */
export const ToolCallDialog = ({
    toolCall,
    onClose,
}: {
    toolCall: ToolCallRecord;
    onClose: () => void;
}) => {
    const isDarkMode = useDarkMode();
    const theme = isDarkMode ? "tomorrow_night" : "github";

    return (
        <Dialog open onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle sx={TITLE_SX}>
                {toolCall.label}
                <IconButton size="small" onClick={onClose} sx={CLOSE_SX}>
                    <Close fontSize="small" />
                </IconButton>
            </DialogTitle>
            <DialogContent dividers>
                <Typography variant="caption" color="text.secondary">
                    Input
                </Typography>
                <Box sx={INPUT_BOX_SX}>
                    <AceEditor
                        mode="json"
                        value={formatJson(toolCall.args)}
                        readOnly
                        width="100%"
                        height="200px"
                        theme={theme}
                        setOptions={{ useWorker: false }}
                        editorProps={{ $blockScrolling: true }}
                    />
                </Box>
                <Typography variant="caption" color="text.secondary">
                    Output
                </Typography>
                <Box sx={OUTPUT_BOX_SX}>
                    <AceEditor
                        mode="json"
                        value={formatJson(toolCall.result)}
                        readOnly
                        width="100%"
                        height="200px"
                        theme={theme}
                        setOptions={{ useWorker: false }}
                        editorProps={{ $blockScrolling: true }}
                    />
                </Box>
            </DialogContent>
        </Dialog>
    );
};
