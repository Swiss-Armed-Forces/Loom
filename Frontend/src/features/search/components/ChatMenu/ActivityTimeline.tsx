import {
    ExpandLess,
    ExpandMore,
    PsychologyOutlined,
} from "@mui/icons-material";
import { Box, CircularProgress, Collapse, Typography } from "@mui/material";
import { useEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import {
    selectShowChatReasoning,
    toggleShowChatReasoning,
} from "@app/slices/searchSlice";

import type { ActivityRecord } from "./ChatWindow.types";
import { ToolCallChip } from "./ToolCallChip";

const ActivityTimelineContent = ({
    activity,
    isActive,
}: {
    activity: ActivityRecord[];
    isActive: boolean;
}) => {
    const containerRef = useRef<HTMLDivElement>(null);
    useEffect(() => {
        if (isActive && containerRef.current) {
            containerRef.current.scrollTop = containerRef.current.scrollHeight;
        }
    }, [activity, isActive]);
    return (
        <Box
            ref={containerRef}
            sx={{
                mt: 0.5,
                p: 1,
                borderLeft: "2px solid",
                borderColor: "divider",
                color: "text.secondary",
                maxHeight: 300,
                overflowY: "auto",
            }}
        >
            {activity.map((entry, i) =>
                entry.type === "reasoning" ? (
                    <Typography
                        key={i}
                        variant="caption"
                        sx={{
                            whiteSpace: "pre-wrap",
                            display: "block",
                            mb: 0.5,
                        }}
                    >
                        {entry.text}
                    </Typography>
                ) : entry.toolCall ? (
                    <Box
                        key={i}
                        sx={{
                            display: "inline-flex",
                            mr: 0.5,
                            mb: 0.5,
                        }}
                    >
                        <ToolCallChip toolCall={entry.toolCall} />
                    </Box>
                ) : null,
            )}
        </Box>
    );
};

export const ActivityTimeline = ({
    activity,
    hasAnswer,
}: {
    activity: ActivityRecord[];
    hasAnswer: boolean;
}) => {
    const dispatch = useDispatch();
    const showLiveThinking = useSelector(selectShowChatReasoning);
    const anyRunning = activity.some(
        (a) => a.type === "tool_call" && a.toolCall?.status === "running",
    );
    const isActive = anyRunning || !hasAnswer;
    // While active: expand based on global preference.
    // Once done: always start collapsed, toggle per-instance.
    const [localExpanded, setLocalExpanded] = useState(false);
    const expanded = isActive ? showLiveThinking : localExpanded;

    const handleClick = () => {
        if (isActive) {
            dispatch(toggleShowChatReasoning());
        } else {
            setLocalExpanded((o) => !o);
        }
    };

    return (
        <Box>
            <Box
                sx={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 0.5,
                    cursor: "pointer",
                    color: "text.secondary",
                    userSelect: "none",
                }}
                onClick={handleClick}
            >
                {isActive ? (
                    <CircularProgress size={12} />
                ) : (
                    <PsychologyOutlined sx={{ fontSize: 14 }} />
                )}
                <Typography variant="caption">
                    {isActive ? "Thinking…" : "Reasoned"}
                </Typography>
                {expanded ? (
                    <ExpandLess sx={{ fontSize: 14 }} />
                ) : (
                    <ExpandMore sx={{ fontSize: 14 }} />
                )}
            </Box>
            <Collapse in={expanded}>
                <ActivityTimelineContent
                    activity={activity}
                    isActive={isActive}
                />
            </Collapse>
        </Box>
    );
};
