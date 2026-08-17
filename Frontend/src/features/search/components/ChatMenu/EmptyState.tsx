import { SmartToy } from "@mui/icons-material";
import { Box, Chip, Typography } from "@mui/material";
import { useState } from "react";

import { ALL_SUGGESTED_QUESTIONS } from "./ChatWindow.types";

export const EmptyState = ({
    query,
    onSuggestedQuestion,
}: {
    query: string | null;
    onSuggestedQuestion: (q: string) => void;
}) => {
    const [suggestedQuestions] = useState(() => {
        const shuffled = [...ALL_SUGGESTED_QUESTIONS].sort(
            () => Math.random() - 0.5,
        );
        return shuffled.slice(0, 3);
    });

    const contextLabel =
        query && query !== "*"
            ? `documents matching "${query}"`
            : "your documents";

    return (
        <Box
            sx={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                minHeight: 200,
                gap: 2,
                p: 3,
                textAlign: "center",
            }}
        >
            <SmartToy
                sx={{
                    fontSize: 44,
                    color: "primary.main",
                    opacity: 0.65,
                }}
            />
            <Typography variant="body2" color="text.secondary">
                {query && query !== "*"
                    ? `I have access to ${contextLabel}. Ask me anything.`
                    : "Ask me anything about your documents."}
            </Typography>
            <Box
                sx={{
                    display: "flex",
                    flexWrap: "wrap",
                    gap: 0.75,
                    justifyContent: "center",
                }}
            >
                {suggestedQuestions.map((q) => (
                    <Chip
                        key={q}
                        label={q}
                        size="small"
                        color="primary"
                        variant="outlined"
                        onClick={() => onSuggestedQuestion(q)}
                        sx={{ cursor: "pointer" }}
                    />
                ))}
            </Box>
        </Box>
    );
};
