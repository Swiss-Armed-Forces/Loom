import { Box, Tooltip } from "@mui/material";
import React, { useEffect, useState } from "react";
import { toast } from "react-toastify";

import {
    ContextCreateResponse,
    createAiContext,
    processQuestion,
} from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import { openDialog, selectLastFileDetailTab } from "@app/slices/commonSlice";
import {
    selectQuery,
    selectWebSocketPubSubMessage,
} from "@app/slices/searchSlice";
import { DialogType } from "@features/common/utils/enums";
import { webSocketSendMessage } from "@middleware/SocketMiddleware";

import styles from "./Chatbot.module.css";
import { ChatWindow } from "./ChatWindow";
import { MessageInput } from "./MessageInput";

interface ChatMessage {
    text: React.ReactNode[];
    isUser: boolean;
    token_ids: string[];
    citations: string[];
}

export const Chatbot = () => {
    const dispatch = useAppDispatch();

    const searchQuery = useAppSelector(selectQuery);
    const webSocketPubSubMessage = useAppSelector(selectWebSocketPubSubMessage);
    const lastTab = useAppSelector(selectLastFileDetailTab);

    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [aiContext, setAiContext] = useState<ContextCreateResponse | null>(
        null,
    );

    useEffect(() => {
        if (!searchQuery) return;
        if (aiContext)
            dispatch(
                webSocketSendMessage({
                    message: {
                        type: "unsubscribe",
                        channels: [aiContext.contextId],
                    },
                }),
            );
        createAiContext(searchQuery).then(setAiContext).catch(toast.error);
    }, [searchQuery]); // eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => {
        if (!aiContext) return;
        setMessages([]);
        // subscribe to context messages
        dispatch(
            webSocketSendMessage({
                message: {
                    type: "subscribe",
                    channels: [aiContext.contextId],
                },
            }),
        );
    }, [aiContext]); // eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => {
        if (!webSocketPubSubMessage) return;
        const msg = webSocketPubSubMessage.message;

        if (msg.type !== "chatBotToken" && msg.type !== "chatBotCitation")
            return;

        const handleViewDetail = (fileId: string) => {
            dispatch(
                openDialog({
                    id: "",
                    type: DialogType.FileDetail,
                    props: { fileId, tab: lastTab },
                }),
            );
        };

        setMessages((prev) => {
            const newMessages = [...prev];
            let lastMessage = newMessages.at(-1);

            // ensure we have an AI message to append to
            if (!lastMessage || lastMessage.isUser) {
                lastMessage = {
                    text: [""],
                    isUser: false,
                    token_ids: [],
                    citations: [],
                };
                newMessages.push(lastMessage);
            }

            if (msg.type === "chatBotToken") {
                // check if we didn't already append the token
                if (lastMessage.token_ids.includes(msg.tokenId)) return prev;

                // add token
                const textIdx = lastMessage.text.length - 1;
                if (typeof lastMessage.text[textIdx] === "string") {
                    lastMessage.text[textIdx] += msg.token;
                } else {
                    lastMessage.text.push(msg.token);
                }
                lastMessage.token_ids.push(msg.tokenId);
            } else if (msg.type === "chatBotCitation") {
                // add citation if not already present
                if (!lastMessage.citations.includes(msg.id)) {
                    const count =
                        lastMessage.text.filter(
                            (elem) => typeof elem !== "string",
                        ).length + 1;

                    lastMessage.text.push(
                        <Tooltip
                            key={msg.id}
                            title={`${msg.text} | Rank: ${msg.rank}`}
                        >
                            <sup>
                                <a
                                    href={`#${msg.fileId}`}
                                    onClick={(e) => {
                                        e.preventDefault();
                                        handleViewDetail(msg.fileId);
                                    }}
                                >
                                    {`[${count}]`}
                                </a>
                            </sup>
                        </Tooltip>,
                    );
                    lastMessage.citations.push(msg.id);
                }
            }

            return newMessages;
        });
    }, [webSocketPubSubMessage]); // eslint-disable-line react-hooks/exhaustive-deps

    const handleSendMessage = async (message: string) => {
        if (!aiContext) return;

        // add user message
        setMessages((prev) => [
            ...prev,
            { text: [message], isUser: true, token_ids: [], citations: [] },
        ]);

        try {
            // generate bot response
            await processQuestion(aiContext, message);
        } catch (err: any) {
            console.error(err);
            toast.error("Cannot get chatbot response");
        }
    };

    return (
        <Box
            className={styles.sticky}
            sx={{
                display: "flex",
                flexDirection: "column",
                height: "95%",
                width: 500,
                padding: 2,
                position: "relative",
            }}
        >
            <Box
                sx={{
                    flexGrow: 1,
                    overflowY: "auto",
                    marginY: 2,
                    height: 600,
                    width: 450,
                    padding: 2,
                    border: "1px solid #ccc",
                    borderRadius: 1,
                }}
            >
                <ChatWindow messages={messages} />
            </Box>
            <Box
                component="form"
                onSubmit={(e) => {
                    e.preventDefault();
                }}
                sx={{
                    position: "relative",
                    display: "flex",
                    padding: "16px",
                    alignItems: "center",
                }}
            >
                <MessageInput
                    disabled={aiContext === null}
                    onSendMessage={handleSendMessage}
                />
            </Box>
        </Box>
    );
};
