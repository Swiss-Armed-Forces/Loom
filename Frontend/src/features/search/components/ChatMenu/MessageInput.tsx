import SendIcon from "@mui/icons-material/Send";
import StopIcon from "@mui/icons-material/Stop";
import { IconButton, InputAdornment, TextField } from "@mui/material";
import { useEffect, useRef, useState } from "react";

interface MessageInputProps {
    disabled: boolean;
    onSendMessage: (message: string) => void;
    onStop: () => void;
}

export const MessageInput = ({
    disabled,
    onSendMessage,
    onStop,
}: MessageInputProps) => {
    const [inputValue, setInputValue] = useState("");
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (!disabled) inputRef.current?.focus();
    }, [disabled]);

    const handleSend = () => {
        if (!inputValue.trim() || disabled) return;
        onSendMessage(inputValue.trim());
        setInputValue("");
    };

    const handleKeyDown = (event: React.KeyboardEvent) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            handleSend();
        }
    };

    const canSend = inputValue.trim().length > 0 && !disabled;

    return (
        <TextField
            fullWidth
            multiline
            maxRows={4}
            size="small"
            disabled={disabled}
            variant="outlined"
            inputRef={inputRef}
            value={inputValue}
            placeholder={
                disabled
                    ? "Thinking…"
                    : "Ask a question… (Shift+Enter for newline)"
            }
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            sx={{
                "& .MuiOutlinedInput-root": {
                    borderRadius: "24px",
                    paddingRight: "6px",
                },
            }}
            slotProps={{
                input: {
                    endAdornment: (
                        <InputAdornment position="end">
                            {disabled ? (
                                <IconButton
                                    color="error"
                                    onClick={onStop}
                                    size="small"
                                >
                                    <StopIcon fontSize="small" />
                                </IconButton>
                            ) : (
                                <IconButton
                                    color="primary"
                                    onClick={handleSend}
                                    disabled={!canSend}
                                    size="small"
                                    sx={{
                                        transition:
                                            "transform 0.15s, opacity 0.15s",
                                        opacity: canSend ? 1 : 0.4,
                                        ...(canSend && {
                                            "&:hover": {
                                                transform: "scale(1.1)",
                                            },
                                        }),
                                    }}
                                >
                                    <SendIcon fontSize="small" />
                                </IconButton>
                            )}
                        </InputAdornment>
                    ),
                },
            }}
        />
    );
};
