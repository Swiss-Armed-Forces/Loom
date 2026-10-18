import {
    ContentCopy,
    ErrorOutlineOutlined,
    ManageSearch,
} from "@mui/icons-material";
import { Box, IconButton, Tooltip, Typography } from "@mui/material";
import { alpha } from "@mui/material/styles";
import type { Theme } from "@mui/material/styles";
import React from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { useAppDispatch } from "@app/hooks";
import { selectQuery, updateQuery } from "@app/slices/searchSlice";
import { store } from "@app/store";
import { SearchQueryField } from "@features/common/utils/enums";
import { updateFieldOfQuery } from "@features/common/utils/helpers/updateFieldOfQuery";

import { ActivityTimeline } from "./ActivityTimeline";
import { AssistantAvatar } from "./AssistantAvatar";
import type { ChatMessage } from "./ChatWindow.types";
import { CitationList } from "./CitationList";
import { MessageMarkdown } from "./MessageMarkdown";

// Every sx below is a module constant rather than an object literal in the
// render body. A literal is a new object on every render, which makes emotion
// re-serialise the whole rule set for every bubble on every token.

const ERROR_BUBBLE_SX = (theme: Theme) => ({
    maxWidth: "82%",
    display: "flex",
    alignItems: "flex-start",
    gap: 0.75,
    px: 1.25,
    py: 0.75,
    borderRadius: "18px 18px 18px 4px",
    bgcolor: alpha(theme.palette.error.main, 0.08),
    border: "1px solid",
    borderColor: alpha(theme.palette.error.main, 0.25),
});

const ERROR_ICON_SX = {
    fontSize: 15,
    color: "error.main",
    mt: 0.1,
    flexShrink: 0,
} as const;

const ERROR_TEXT_SX = { whiteSpace: "pre-wrap" } as const;

const COLUMN_SX = {
    maxWidth: "82%",
    minWidth: 0,
    display: "flex",
    flexDirection: "column",
    "&:hover .hover-action": { opacity: 1 },
} as const;

const USER_COLUMN_SX = { ...COLUMN_SX, alignItems: "flex-end" } as const;
const ASSISTANT_COLUMN_SX = { ...COLUMN_SX, alignItems: "flex-start" } as const;

/** Styling for the markdown react-markdown produces inside a bubble. */
const MARKDOWN_CONTENT_SX = {
    overflowWrap: "break-word",
    "& p": { m: 0 },
    "& p + p": { mt: 1 },
    "& pre": {
        m: 0,
        mt: 0.5,
        mb: 0.5,
        p: 1,
        borderRadius: 1,
        bgcolor: "rgba(0,0,0,0.12)",
        overflowX: "auto",
        fontSize: "0.75rem",
        fontFamily: "monospace",
        whiteSpace: "pre",
    },
    "& code": {
        fontFamily: "monospace",
        fontSize: "0.8em",
        px: 0.4,
        borderRadius: 0.5,
        bgcolor: "rgba(0,0,0,0.10)",
    },
    "& pre code": {
        bgcolor: "transparent",
        px: 0,
    },
    "& ul, & ol": {
        pl: 2.5,
        my: 0.5,
    },
    "& li": { mb: 0.25 },
    "& h1, & h2, & h3": {
        mt: 1,
        mb: 0.5,
        fontWeight: 600,
        fontSize: "0.9rem",
    },
    "& table": {
        borderCollapse: "collapse",
        width: "100%",
        my: 0.5,
        fontSize: "0.8rem",
        display: "block",
        overflowX: "auto",
    },
    "& th, & td": {
        border: "1px solid",
        borderColor: "divider",
        px: 1,
        py: 0.5,
        textAlign: "left",
    },
    "& th": {
        fontWeight: 600,
        bgcolor: "rgba(0,0,0,0.06)",
    },
    "& del": {
        textDecoration: "line-through",
    },
    "& input[type='checkbox']": {
        mr: 0.5,
    },
    "& blockquote": {
        m: 0,
        mt: 0.5,
        pl: 1,
        borderLeft: "3px solid",
        borderColor: "divider",
    },
} as const;

const USER_BUBBLE_SX = (theme: Theme) => ({
    maxWidth: "100%",
    backgroundColor: theme.palette.primary.main,
    color: theme.palette.primary.contrastText,
    borderRadius: "18px 18px 4px 18px",
    px: 1.5,
    py: 0.75,
    boxShadow: "0 1px 4px rgba(0,0,0,0.15)",
    ...MARKDOWN_CONTENT_SX,
});

const ASSISTANT_BUBBLE_SX = (theme: Theme) => ({
    maxWidth: "100%",
    backgroundColor: theme.vars
        ? `rgba(${theme.vars.palette.text.primaryChannel} / 0.08)`
        : alpha(theme.palette.text.primary, 0.08),
    color: theme.vars?.palette.text.primary ?? theme.palette.text.primary,
    borderRadius: "18px 18px 18px 4px",
    px: 1.5,
    py: 0.75,
    boxShadow: "none",
    ...MARKDOWN_CONTENT_SX,
});

const ACTIONS_SX = { display: "flex", gap: 0.5, mt: 0.25 } as const;

const ACTION_BUTTON_SX = {
    opacity: 0,
    transition: "opacity 0.15s",
    fontSize: 14,
} as const;

const ACTIVITY_WITH_ANSWER_SX = { mb: 0.75 } as const;
const ACTIVITY_ONLY_SX = { mb: 0 } as const;

export const MessageBubble = React.memo(
    ({ message }: { message: ChatMessage }) => {
        const { t } = useTranslation();
        const dispatch = useAppDispatch();

        const handleCopy = () => {
            navigator.clipboard.writeText(message.text).then(
                () => toast.success(t("chatbot.messageCopied")),
                () => toast.error(t("chatbot.copyFailed")),
            );
        };

        const handleShowSources = (e: React.MouseEvent) => {
            const negate = e.shiftKey;
            const accumulate = e.ctrlKey;
            const uniqueFileIds = [
                ...new Set(message.citations.map((c) => c.fileId)),
            ];
            // Read on click rather than subscribing: a selector here would
            // re-render every bubble in the thread whenever the query changes.
            const currentQuery = selectQuery(store.getState());
            const query = updateFieldOfQuery(
                currentQuery?.query ?? "",
                SearchQueryField.Id,
                uniqueFileIds,
                false,
                negate,
                accumulate,
                [],
                true,
            );
            dispatch(updateQuery({ query }));
        };

        if (message.isError) {
            return (
                <>
                    <AssistantAvatar />
                    <Box sx={ERROR_BUBBLE_SX}>
                        <ErrorOutlineOutlined sx={ERROR_ICON_SX} />
                        <Typography
                            variant="body2"
                            color="error.main"
                            sx={ERROR_TEXT_SX}
                        >
                            {message.text}
                        </Typography>
                    </Box>
                </>
            );
        }

        const hasActivity = !message.isUser && !!message.activity?.length;

        return (
            <>
                {!message.isUser && <AssistantAvatar />}
                <Box sx={message.isUser ? USER_COLUMN_SX : ASSISTANT_COLUMN_SX}>
                    <Box
                        sx={
                            message.isUser
                                ? USER_BUBBLE_SX
                                : ASSISTANT_BUBBLE_SX
                        }
                    >
                        {hasActivity && (
                            <Box
                                sx={
                                    message.text
                                        ? ACTIVITY_WITH_ANSWER_SX
                                        : ACTIVITY_ONLY_SX
                                }
                            >
                                <ActivityTimeline
                                    activity={message.activity ?? []}
                                    hasAnswer={!!message.text}
                                />
                            </Box>
                        )}
                        {message.text && (
                            <MessageMarkdown text={message.text} />
                        )}
                        {!message.isUser && (
                            <CitationList citations={message.citations} />
                        )}
                    </Box>
                    {!message.isUser && (
                        <Box sx={ACTIONS_SX}>
                            <Tooltip
                                title={t("chatbot.copyMessage")}
                                placement="top"
                            >
                                <IconButton
                                    className="hover-action"
                                    size="small"
                                    onClick={handleCopy}
                                    sx={ACTION_BUTTON_SX}
                                >
                                    <ContentCopy fontSize="inherit" />
                                </IconButton>
                            </Tooltip>
                            {message.citations.length > 0 && (
                                <Tooltip
                                    title={t("chatbot.showSourcesInSearch")}
                                    placement="top"
                                >
                                    <IconButton
                                        className="hover-action"
                                        size="small"
                                        onClick={handleShowSources}
                                        sx={ACTION_BUTTON_SX}
                                    >
                                        <ManageSearch fontSize="inherit" />
                                    </IconButton>
                                </Tooltip>
                            )}
                        </Box>
                    )}
                </Box>
            </>
        );
    },
);
MessageBubble.displayName = "MessageBubble";
