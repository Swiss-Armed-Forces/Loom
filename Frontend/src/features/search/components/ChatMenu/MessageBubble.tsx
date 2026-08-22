import {
    ContentCopy,
    ErrorOutlineOutlined,
    ManageSearch,
} from "@mui/icons-material";
import { Box, IconButton, Tooltip, Typography } from "@mui/material";
import { alpha, useTheme } from "@mui/material/styles";
import React from "react";
import { useTranslation } from "react-i18next";
import Markdown from "react-markdown";
import { toast } from "react-toastify";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";

import "./hljs-theme";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import { selectQuery, updateQuery } from "@app/slices/searchSlice";
import { SearchQueryField } from "@features/common/utils/enums";
import { updateFieldOfQuery } from "@features/common/utils/helpers/updateFieldOfQuery";

import { ActivityTimeline } from "./ActivityTimeline";
import { AssistantAvatar } from "./AssistantAvatar";
import type { ChatMessage } from "./ChatWindow.types";
import { CitationList } from "./CitationList";

const REMARK_PLUGINS = [remarkGfm];
const REHYPE_PLUGINS = [rehypeHighlight];

export const MessageBubble = React.memo(
    ({ message }: { message: ChatMessage }) => {
        const theme = useTheme();
        const { t } = useTranslation();
        const dispatch = useAppDispatch();
        const currentQuery = useAppSelector(selectQuery);

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

        return (
            <>
                {!message.isUser && <AssistantAvatar />}
                {message.isError ? (
                    <Box
                        sx={{
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
                        }}
                    >
                        <ErrorOutlineOutlined
                            sx={{
                                fontSize: 15,
                                color: "error.main",
                                mt: 0.1,
                                flexShrink: 0,
                            }}
                        />
                        <Typography
                            variant="body2"
                            color="error.main"
                            sx={{ whiteSpace: "pre-wrap" }}
                        >
                            {message.text}
                        </Typography>
                    </Box>
                ) : (
                    <Box
                        sx={{
                            maxWidth: "82%",
                            minWidth: 0,
                            display: "flex",
                            flexDirection: "column",
                            alignItems: message.isUser
                                ? "flex-end"
                                : "flex-start",
                            "&:hover .hover-action": { opacity: 1 },
                        }}
                    >
                        <Box
                            sx={{
                                maxWidth: "100%",
                                backgroundColor: message.isUser
                                    ? theme.palette.primary.main
                                    : theme.vars
                                      ? `rgba(${theme.vars.palette.text.primaryChannel} / 0.08)`
                                      : alpha(theme.palette.text.primary, 0.08),
                                color: message.isUser
                                    ? theme.palette.primary.contrastText
                                    : (theme.vars?.palette.text.primary ??
                                      theme.palette.text.primary),
                                borderRadius: message.isUser
                                    ? "18px 18px 4px 18px"
                                    : "18px 18px 18px 4px",
                                px: 1.5,
                                py: 0.75,
                                boxShadow: message.isUser
                                    ? "0 1px 4px rgba(0,0,0,0.15)"
                                    : "none",
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
                            }}
                        >
                            {!message.isUser &&
                                message.activity &&
                                message.activity.length > 0 && (
                                    <Box
                                        sx={{
                                            mb: message.text ? 0.75 : 0,
                                        }}
                                    >
                                        <ActivityTimeline
                                            activity={message.activity}
                                            hasAnswer={!!message.text}
                                        />
                                    </Box>
                                )}
                            {message.text && (
                                <Typography variant="body2" component="div">
                                    <Markdown
                                        remarkPlugins={REMARK_PLUGINS}
                                        rehypePlugins={REHYPE_PLUGINS}
                                    >
                                        {message.text}
                                    </Markdown>
                                </Typography>
                            )}
                            {!message.isUser && (
                                <CitationList citations={message.citations} />
                            )}
                        </Box>
                        {!message.isUser && (
                            <Box
                                sx={{
                                    display: "flex",
                                    gap: 0.5,
                                    mt: 0.25,
                                }}
                            >
                                <Tooltip
                                    title={t("chatbot.copyMessage")}
                                    placement="top"
                                >
                                    <IconButton
                                        className="hover-action"
                                        size="small"
                                        onClick={handleCopy}
                                        sx={{
                                            opacity: 0,
                                            transition: "opacity 0.15s",
                                            fontSize: 14,
                                        }}
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
                                            sx={{
                                                opacity: 0,
                                                transition: "opacity 0.15s",
                                                fontSize: 14,
                                            }}
                                        >
                                            <ManageSearch fontSize="inherit" />
                                        </IconButton>
                                    </Tooltip>
                                )}
                            </Box>
                        )}
                    </Box>
                )}
            </>
        );
    },
);
MessageBubble.displayName = "MessageBubble";
