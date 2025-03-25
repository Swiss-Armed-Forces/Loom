import { createTheme } from "@mui/material";

export const globalTheme = createTheme({
    components: {
        MuiButton: {
            styleOverrides: {
                root: {
                    textTransform: "none",
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
