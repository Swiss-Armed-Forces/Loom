import { useMediaQuery } from "@mui/material";

export const useDarkMode = (): boolean => {
    return useMediaQuery("(prefers-color-scheme: dark)");
};
