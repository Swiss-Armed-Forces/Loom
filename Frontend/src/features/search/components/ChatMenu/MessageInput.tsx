import SendIcon from "@mui/icons-material/Send";
import { TextField, IconButton, Tooltip } from "@mui/material";
import { useState } from "react";

interface MessageInputProps {
    disabled: boolean;
    onSendMessage: (message: string) => void;
}

export const MessageInput = ({
    disabled,
    onSendMessage,
}: MessageInputProps) => {
    const [inputValue, setInputValue] = useState("");

    const handleSendClick = () => {
        if (!inputValue.trim()) return;
        onSendMessage(inputValue);
        setInputValue("");
    };

    const handleKeyPress = (event: { key: string }) => {
        if (event.key === "Enter") handleSendClick();
    };

    return (
        <>
            <TextField
                fullWidth
                disabled={disabled}
                variant="outlined"
                value={inputValue}
                onChange={(e) => {
                    setInputValue(e.target.value);
                }}
                onKeyUp={handleKeyPress}
                sx={{ flexGrow: 1, marginRight: "16px" }} // This will make the TextField expand
            />
            <Tooltip title="Send question">
                <IconButton
                    color="primary"
                    onClick={handleSendClick}
                    sx={{ flexShrink: 0 }}
                >
                    <SendIcon />
                </IconButton>
            </Tooltip>
        </>
    );
};
