import { Forum, VisibilityOff } from "@mui/icons-material";
import {
    Box,
    CircularProgress,
    IconButton,
    InputAdornment,
    List,
    ListItem,
    ListItemButton,
    ListItemText,
    TextField,
    Tooltip,
    Typography,
} from "@mui/material";

import { ChatbotInner } from "./ChatbotInner";
import type { UseChatbotResult } from "./useChatbot";

interface ChatbotProps {
    chatbot: UseChatbotResult;
}

export const Chatbot = ({ chatbot }: ChatbotProps) => {
    const {
        activeContext,
        showHistory,
        historySearch,
        filteredContexts,
        setHistorySearch,
        handleSelectContext,
        handleHideContext,
        refreshContexts,
        isHidden,
    } = chatbot;

    return (
        <Box
            sx={{
                display: "flex",
                flexDirection: "column",
                height: "100%",
                overflow: "hidden",
            }}
        >
            {showHistory ? (
                <Box
                    sx={{
                        display: "flex",
                        flexDirection: "column",
                        flex: 1,
                        overflow: "hidden",
                    }}
                >
                    <Box sx={{ px: 1, py: 0.75, flexShrink: 0 }}>
                        <TextField
                            size="small"
                            fullWidth
                            placeholder="Search conversations…"
                            value={historySearch}
                            onChange={(e) => setHistorySearch(e.target.value)}
                            slotProps={{
                                input: {
                                    startAdornment: (
                                        <InputAdornment position="start">
                                            <Forum
                                                fontSize="small"
                                                color="disabled"
                                            />
                                        </InputAdornment>
                                    ),
                                },
                            }}
                        />
                    </Box>
                    <List dense sx={{ flex: 1, overflowY: "auto", py: 0 }}>
                        {filteredContexts.map((ctx) => (
                            <ListItem
                                key={ctx.contextId}
                                disablePadding
                                secondaryAction={
                                    <Tooltip title="Hide from this list (the conversation stays stored)">
                                        <IconButton
                                            size="small"
                                            edge="end"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleHideContext(
                                                    ctx.contextId,
                                                );
                                            }}
                                        >
                                            <VisibilityOff fontSize="small" />
                                        </IconButton>
                                    </Tooltip>
                                }
                            >
                                <ListItemButton
                                    selected={
                                        activeContext?.contextId ===
                                        ctx.contextId
                                    }
                                    onClick={() =>
                                        handleSelectContext(ctx.contextId)
                                    }
                                    sx={{ pr: 5 }}
                                >
                                    <ListItemText
                                        primary={
                                            ctx.firstQuestion ??
                                            "New conversation"
                                        }
                                        secondary={ctx.createdAt.toLocaleDateString()}
                                        slotProps={{
                                            primary: {
                                                noWrap: true,
                                                variant: "body2",
                                            },
                                            secondary: {
                                                variant: "caption",
                                            },
                                        }}
                                    />
                                </ListItemButton>
                            </ListItem>
                        ))}
                        {filteredContexts.length === 0 && (
                            <Box sx={{ p: 2, textAlign: "center" }}>
                                <Typography
                                    variant="body2"
                                    color="text.secondary"
                                >
                                    {historySearch
                                        ? "No matching conversations"
                                        : "No conversations yet"}
                                </Typography>
                            </Box>
                        )}
                    </List>
                </Box>
            ) : activeContext ? (
                <ChatbotInner
                    key={activeContext.contextId}
                    contextId={activeContext.contextId}
                    onRunComplete={refreshContexts}
                    isHidden={isHidden}
                />
            ) : (
                <Box
                    sx={{
                        flexGrow: 1,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                    }}
                >
                    <CircularProgress size={24} />
                </Box>
            )}
        </Box>
    );
};
