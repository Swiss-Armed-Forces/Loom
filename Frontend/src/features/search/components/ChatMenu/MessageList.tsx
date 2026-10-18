import { ListItem } from "@mui/material";
import React from "react";

import type { ChatMessage } from "./ChatWindow.types";
import { MessageBubble } from "./MessageBubble";

const ITEM_SX = {
    alignItems: "flex-end",
    px: 0.5,
    py: 0.5,
} as const;

const USER_ITEM_SX = { ...ITEM_SX, justifyContent: "flex-end" } as const;
const ASSISTANT_ITEM_SX = { ...ITEM_SX, justifyContent: "flex-start" } as const;

/**
 * The conversation so far.
 *
 * Memoised on `messages` alone, and `mapToChatMessages` preserves the object
 * of every message it did not change, so a streamed token re-renders one
 * bubble instead of re-parsing the markdown of the whole thread.
 */
export const MessageList = React.memo(
    ({ messages }: { messages: ChatMessage[] }) => (
        <>
            {messages.map((message, index) => (
                <ListItem
                    key={message.id ?? `fallback-${index}`}
                    sx={message.isUser ? USER_ITEM_SX : ASSISTANT_ITEM_SX}
                >
                    <MessageBubble message={message} />
                </ListItem>
            ))}
        </>
    ),
);
MessageList.displayName = "MessageList";
