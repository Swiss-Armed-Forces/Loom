import { Box, Chip, Typography } from "@mui/material";
import { alpha, useTheme } from "@mui/material/styles";

import { AssistantAvatar } from "./AssistantAvatar";

export const PendingQuestion = ({
    question,
    options,
    onAnswer,
}: {
    question: string;
    options: string[];
    onAnswer: (answer: string) => void;
}) => {
    const theme = useTheme();

    return (
        <>
            <AssistantAvatar />
            <Box sx={{ maxWidth: "82%" }}>
                <Box
                    sx={{
                        backgroundColor: theme.vars
                            ? `rgba(${theme.vars.palette.text.primaryChannel} / 0.08)`
                            : alpha(theme.palette.text.primary, 0.08),
                        borderRadius: "18px 18px 18px 4px",
                        px: 1.5,
                        py: 0.75,
                    }}
                >
                    <Typography variant="body2">{question}</Typography>
                </Box>
                <Box
                    sx={{
                        display: "flex",
                        flexWrap: "wrap",
                        gap: 0.75,
                        mt: 0.75,
                    }}
                >
                    {options.map((opt) => (
                        <Chip
                            key={opt}
                            label={opt}
                            size="small"
                            variant="outlined"
                            color="primary"
                            onClick={() => onAnswer(opt)}
                            clickable
                        />
                    ))}
                </Box>
            </Box>
        </>
    );
};
