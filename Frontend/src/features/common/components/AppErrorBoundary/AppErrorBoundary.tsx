import { Alert, AlertTitle, Box, Button } from "@mui/material";
import { t } from "i18next";
import { Component, ErrorInfo, ReactNode } from "react";

interface AppErrorBoundaryProps {
    children: ReactNode;
}

interface AppErrorBoundaryState {
    error: Error | null;
}

/**
 * Last line between one thrown render and a blank page.
 *
 * React's answer to an uncaught error during render is to unmount the whole
 * tree, so without this any one component - a header status widget reading a
 * field the API stopped sending, say - takes Loom down to an empty document
 * with nothing on screen to say why. The boundary keeps the page, names the
 * error and offers a reload.
 */
export class AppErrorBoundary extends Component<
    AppErrorBoundaryProps,
    AppErrorBoundaryState
> {
    state: AppErrorBoundaryState = { error: null };

    static getDerivedStateFromError(error: Error): AppErrorBoundaryState {
        return { error };
    }

    componentDidCatch(error: Error, info: ErrorInfo) {
        // The stack is the only record of where this came from; the overlay
        // below deliberately shows the message alone.
        console.error("Unhandled render error", error, info.componentStack);
    }

    render() {
        const { error } = this.state;
        if (!error) return this.props.children;
        return (
            <Box sx={{ p: 3, display: "flex", justifyContent: "center" }}>
                <Alert
                    severity="error"
                    sx={{ maxWidth: "48rem", width: "100%" }}
                    action={
                        <Button
                            color="inherit"
                            size="small"
                            onClick={() => window.location.reload()}
                        >
                            {t("error.boundaryReload")}
                        </Button>
                    }
                >
                    <AlertTitle>{t("error.boundaryTitle")}</AlertTitle>
                    {t("error.boundaryDescription")}
                    <Box
                        component="pre"
                        sx={{
                            mt: 1,
                            mb: 0,
                            whiteSpace: "pre-wrap",
                            wordBreak: "break-word",
                            fontSize: "0.78rem",
                        }}
                    >
                        {error.message}
                    </Box>
                </Alert>
            </Box>
        );
    }
}
