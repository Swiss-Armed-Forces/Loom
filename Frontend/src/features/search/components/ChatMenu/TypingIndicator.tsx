import { Box } from "@mui/material";
import { useTheme } from "@mui/material/styles";

const CONTAINER_SX = {
    display: "flex",
    gap: 0.5,
    alignItems: "center",
    p: 0.5,
} as const;

// Declared once rather than inside each dot's sx, where emotion re-serialises
// the keyframe block for every dot on every render.
const DOT_SX = {
    width: 7,
    height: 7,
    borderRadius: "50%",
    animation: "chatBounce 1.2s infinite ease-in-out",
    "@keyframes chatBounce": {
        "0%, 80%, 100%": {
            transform: "scale(0.6)",
            opacity: 0.4,
        },
        "40%": { transform: "scale(1)", opacity: 1 },
    },
} as const;

const DOT_DELAYS = ["0s", "0.2s", "0.4s"] as const;

export const TypingIndicator = ({
    color,
}: {
    color?: "primary" | "secondary";
} = {}) => {
    const theme = useTheme();
    const dotColor = color
        ? (theme.vars?.palette[color].main ?? theme.palette[color].main)
        : (theme.vars?.palette.text.secondary ?? theme.palette.text.secondary);
    return (
        <Box sx={CONTAINER_SX}>
            {DOT_DELAYS.map((delay) => (
                <Box
                    key={delay}
                    sx={{
                        ...DOT_SX,
                        bgcolor: dotColor,
                        animationDelay: delay,
                    }}
                />
            ))}
        </Box>
    );
};
