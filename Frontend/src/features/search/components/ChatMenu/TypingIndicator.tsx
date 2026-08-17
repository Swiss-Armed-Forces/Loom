import { Box } from "@mui/material";
import { useTheme } from "@mui/material/styles";

export const TypingIndicator = () => {
    const theme = useTheme();
    return (
        <Box sx={{ display: "flex", gap: 0.5, alignItems: "center", p: 0.5 }}>
            {[0, 1, 2].map((i) => (
                <Box
                    key={i}
                    sx={{
                        width: 7,
                        height: 7,
                        borderRadius: "50%",
                        bgcolor:
                            theme.vars?.palette.text.secondary ??
                            theme.palette.text.secondary,
                        animation: "chatBounce 1.2s infinite ease-in-out",
                        animationDelay: `${i * 0.2}s`,
                        "@keyframes chatBounce": {
                            "0%, 80%, 100%": {
                                transform: "scale(0.6)",
                                opacity: 0.4,
                            },
                            "40%": { transform: "scale(1)", opacity: 1 },
                        },
                    }}
                />
            ))}
        </Box>
    );
};
