import React, { useEffect, useState } from "react";
import { Box, Tooltip } from "@mui/material";
import ChatWindow from "./ChatWindow";
import MessageInput from "./MessageInput";
import styles from "./Chatbot.module.css";
import { selectQuery, selectWebSocketPubSubMessage } from "../searchSlice";
import { useAppDispatch, useAppSelector } from "../../../app/hooks";
import { toast } from "react-toastify";
import {
    ContextCreateResponse,
    createAiContext,
    processQuestion,
} from "../../../app/api";
import { webSocketSendMessage } from "../../../middleware/SocketMiddleware";
import { showFileDetailDialog } from "../../common/commonSlice";

// eslint-disable-next-line @typescript-eslint/no-empty-object-type
interface ChatbotProps {}

interface ChatMessage {
    text: React.ReactNode[];
    isUser: boolean;
    token_ids: string[];
    citations: string[];
}

const Chatbot: React.FC<ChatbotProps> = () => {
    const dispatch = useAppDispatch();

    const searchQuery = useAppSelector(selectQuery);
    const webSocketPubSubMessage = useAppSelector(selectWebSocketPubSubMessage);

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
        // flush messages
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
        if (webSocketPubSubMessage.message.type !== "chatBotToken") return;
        // append to last message
        let lastMessage = messages.at(-1);
        if (!lastMessage || lastMessage?.isUser) {
            // no last message
            lastMessage = {
                text: [""],
                isUser: false,
                token_ids: [],
                citations: [],
            };
            messages.push(lastMessage);
        }

        // check if we didn't already append the token,
        // this might happen when this function is called
        // multiple times in strict mode
        if (
            lastMessage.token_ids.indexOf(
                webSocketPubSubMessage.message.tokenId,
            ) !== -1
        )
            return;

        // add token
        if (typeof lastMessage.text[lastMessage.text.length - 1] === "string") {
            lastMessage.text[lastMessage.text.length - 1] +=
                webSocketPubSubMessage.message.token;
        } else {
            lastMessage.text.push(webSocketPubSubMessage.message.token);
        }
        lastMessage.token_ids.push(webSocketPubSubMessage.message.tokenId);
        // trigger a reload of the messages
        setMessages([...messages]);
    }, [webSocketPubSubMessage]); // eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => {
        if (!webSocketPubSubMessage) return;
        if (webSocketPubSubMessage.message.type !== "chatBotCitation") return;
        // append to last message
        let lastMessage = messages.at(-1);
        if (!lastMessage || lastMessage?.isUser) {
            // no last message
            lastMessage = {
                text: [""],
                isUser: false,
                token_ids: [],
                citations: [],
            };
            messages.push(lastMessage);
        }

        // add token
        if (
            !lastMessage.citations.includes(webSocketPubSubMessage.message.id)
        ) {
            const fileId = webSocketPubSubMessage.message.fileId;
            const fileText = webSocketPubSubMessage.message.text;
            const count =
                lastMessage.text.filter((elem) => typeof elem !== "string")
                    .length + 1;
            lastMessage.text.push(
                <Tooltip
                    title={
                        fileText +
                        " | Rank: " +
                        webSocketPubSubMessage.message.rank
                    }
                >
                    <sup key={webSocketPubSubMessage.message.id}>
                        <a
                            href={"#" + fileId}
                            onClick={() => {
                                dispatch(showFileDetailDialog({ fileId }));
                            }}
                        >
                            {"[" + count + "]"}
                        </a>
                    </sup>
                </Tooltip>,
            );
            lastMessage.citations.push(webSocketPubSubMessage.message.id);
        }
        // trigger a reload of the messages
        setMessages([...messages]);
    }, [webSocketPubSubMessage]); // eslint-disable-line react-hooks/exhaustive-deps

    const handleSendMessage = async (message: string) => {
        if (!aiContext) return;

        // add user message
        setMessages([
            ...messages,
            { text: [message], isUser: true, token_ids: [], citations: [] },
        ]);

        try {
            // generate bot response
            await processQuestion(aiContext, message!);
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
                position="relative"
                sx={{
                    display: "flex",
                    padding: "16px",
                    alignItems: "center",
                }}
                onSubmit={(e) => {
                    e.preventDefault();
                    //handleSendMessage(e.currentTarget.message.value);
                    //e.currentTarget.message.value = "";
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

export default Chatbot;
