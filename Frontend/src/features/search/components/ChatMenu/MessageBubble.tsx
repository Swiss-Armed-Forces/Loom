import { ErrorOutlineOutlined } from "@mui/icons-material";
import { Box, Typography } from "@mui/material";
import { alpha, useTheme } from "@mui/material/styles";
import Markdown from "react-markdown";

import { ActivityTimeline } from "./ActivityTimeline";
import { AssistantAvatar } from "./AssistantAvatar";
import type { ChatMessage } from "./ChatWindow.types";
import { CitationList } from "./CitationList";

export const MessageBubble = ({
    message,
    onCitationClick,
}: {
    message: ChatMessage;
    onCitationClick: (fileId: string) => void;
}) => {
    const theme = useTheme();

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
                            <Markdown>{message.text}</Markdown>
                        </Typography>
                    )}
                    {!message.isUser && (
                        <CitationList
                            citations={message.citations}
                            onCitationClick={onCitationClick}
                        />
                    )}
                </Box>
            )}
        </>
    );
};
