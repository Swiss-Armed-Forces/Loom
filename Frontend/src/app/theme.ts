import { createTheme } from "@mui/material";

export const globalTheme = createTheme({
    cssVariables: true,
    transitions: {
        create: () => "none",
    },
    components: {
        MuiButton: {
            styleOverrides: {
                root: {
                    textTransform: "none",
                },
            },
        },
        // Canonical hover style for all clickable icons.
        // All clickable icons must use IconButton and must not add custom
        // hover transforms or opacity changes in their own sx props.
        MuiIconButton: {
            styleOverrides: {
                root: {
                    transition: "transform 0.2s ease, opacity 0.2s ease",
                    "&:hover": {
                        backgroundColor: "var(--mui-palette-action-hover)",
                        transform: "scale(1.1)",
                        opacity: 0.8,
                    },
                },
            },
        },
    },
    palette: {
        primary: {
            main: "#FFBF00",
            dark: "#c29400",
        },
        secondary: {
            main: "#31312e",
            dark: "#1c1c1a",
        },
        success: {
            main: "#00c851",
            dark: "#007e33",
        },
        error: {
            main: "#ff4444",
            dark: "#cc0000",
        },
        warning: {
            main: "#ffbb33",
            dark: "#ff8800",
        },
        info: {
            main: "#33b5e5",
            dark: "#0099cc",
        },
    },
});
