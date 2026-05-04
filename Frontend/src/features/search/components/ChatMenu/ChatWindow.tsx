import { List, ListItem, ListItemText } from "@mui/material";
import React, { useRef, useEffect } from "react";

interface ChatWindowProps {
    messages: {
        text: React.ReactNode[];
        isUser: boolean;
        token_ids: string[];
    }[];
}

export const ChatWindow = ({ messages }: ChatWindowProps) => {
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    return (
        <>
            <List>
                {messages.map((message, index) => (
                    <ListItem
                        key={index}
                        style={{
                            justifyContent: message.isUser
                                ? "flex-end"
                                : "flex-start",
                        }}
                    >
                        <ListItemText
                            primary={message.text}
                            style={{
                                backgroundColor: message.isUser
                                    ? "#d1f4ff"
                                    : "#e0e0e0",
                                borderRadius: "10px",
                                padding: "8px 12px",
                            }}
                        />
                    </ListItem>
                ))}
            </List>
            <div ref={messagesEndRef} />
        </>
    );
};
