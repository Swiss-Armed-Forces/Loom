import { Chip, CircularProgress } from "@mui/material";
import React, { useState } from "react";

import type { ToolCallRecord } from "./ChatWindow.types";
// Imported statically on purpose. Pulling this in with React.lazy splits
// ace-builds' esm-resolver into its own chunk, which then evaluates before
// ace defines its global and takes the whole app down with
// "ReferenceError: ace is not defined". It buys nothing either way, because
// FileDetailPanel already imports ace-builds eagerly.
import { ToolCallDialog } from "./ToolCallDialog";

const CHIP_SX = {
    fontSize: "0.7rem",
    height: 22,
    "& .MuiChip-icon": { fontSize: 10 },
} as const;

const RUNNING_CHIP_SX = { ...CHIP_SX, cursor: "default" } as const;
const DONE_CHIP_SX = { ...CHIP_SX, cursor: "pointer" } as const;

export const ToolCallChip = React.memo(
    ({ toolCall }: { toolCall: ToolCallRecord }) => {
        const [open, setOpen] = useState(false);
        const running = toolCall.status === "running";

        return (
            <>
                <Chip
                    label={toolCall.label}
                    size="small"
                    variant="outlined"
                    icon={running ? <CircularProgress size={10} /> : undefined}
                    onClick={running ? undefined : () => setOpen(true)}
                    sx={running ? RUNNING_CHIP_SX : DONE_CHIP_SX}
                />
                {open && (
                    <ToolCallDialog
                        toolCall={toolCall}
                        onClose={() => setOpen(false)}
                    />
                )}
            </>
        );
    },
);
ToolCallChip.displayName = "ToolCallChip";
