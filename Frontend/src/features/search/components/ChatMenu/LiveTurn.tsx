import { Box } from "@mui/material";
import { alpha, useTheme } from "@mui/material/styles";

import { ActivityTimeline } from "./ActivityTimeline";
import { AssistantAvatar } from "./AssistantAvatar";
import type { ActivityRecord } from "./ChatWindow.types";

/**
 * The reasoning and tool calls of the turn currently running, shown above the
 * answer until it starts streaming.
 *
 * This is deliberately a sibling of the message list rather than an entry in
 * it: reasoning arrives one delta at a time, and appending it to the list
 * would hand every bubble a new identity on every delta.
 */
export const LiveTurn = ({
    activity,
    reasoningText,
    isThinking,
}: {
    activity: ActivityRecord[];
    reasoningText: string;
    isThinking: boolean;
}) => {
    const theme = useTheme();

    const entries = isThinking
        ? [...activity, { type: "reasoning" as const, text: reasoningText }]
        : activity;

    if (entries.length === 0) return null;

    return (
        <>
            <AssistantAvatar />
            <Box
                sx={{
                    maxWidth: "82%",
                    backgroundColor: theme.vars
                        ? `rgba(${theme.vars.palette.text.primaryChannel} / 0.08)`
                        : alpha(theme.palette.text.primary, 0.08),
                    borderRadius: "18px 18px 18px 4px",
                    px: 1.5,
                    py: 0.75,
                }}
            >
                <ActivityTimeline activity={entries} hasAnswer={false} />
            </Box>
        </>
    );
};
