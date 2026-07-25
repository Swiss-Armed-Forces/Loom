import {
    CheckCircleOutlined,
    Close,
    InfoOutlined,
    RocketLaunch,
    ScienceOutlined,
} from "@mui/icons-material";
import {
    Alert,
    AlertTitle,
    Box,
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    IconButton,
    Link,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    Paper,
    Stack,
    Typography,
} from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import styles from "./DemoModeIndicator.module.css";

export const DemoModeIndicator = () => {
    const [open, setOpen] = useState(true);
    const { t } = useTranslation();
    const capabilities = [
        t("demoMode.capabilities.search"),
        t("demoMode.capabilities.organize"),
        t("demoMode.capabilities.automation"),
    ];

    const handleClose = () => {
        setOpen(false);
    };

    return (
        <>
            <div className={styles.corner}>
                <button
                    className={styles.ribbon}
                    type="button"
                    aria-haspopup="dialog"
                    aria-expanded={open}
                    aria-controls="demo-mode-dialog"
                    onClick={() => setOpen(true)}
                >
                    {t("demoMode.indicator")}
                </button>
            </div>
            <Dialog
                id="demo-mode-dialog"
                open={open}
                fullWidth
                maxWidth="sm"
                onClose={handleClose}
                aria-labelledby="demo-mode-dialog-title"
                aria-describedby="demo-mode-dialog-introduction"
            >
                <DialogTitle>
                    <Stack
                        direction="row"
                        spacing={1.5}
                        sx={{ alignItems: "center" }}
                    >
                        <Box
                            sx={{
                                alignItems: "center",
                                bgcolor: "primary.main",
                                borderRadius: "50%",
                                color: "secondary.main",
                                display: "flex",
                                flex: "0 0 auto",
                                height: 40,
                                justifyContent: "center",
                                width: 40,
                            }}
                        >
                            <ScienceOutlined aria-hidden="true" />
                        </Box>
                        <Typography
                            id="demo-mode-dialog-title"
                            component="span"
                            variant="h6"
                        >
                            {t("demoMode.title")}
                        </Typography>
                    </Stack>
                    <IconButton
                        aria-label={t("common.close")}
                        title={t("common.close")}
                        onClick={handleClose}
                        sx={{
                            position: "absolute",
                            right: 8,
                            top: 8,
                            color: (theme) => theme.palette.grey[500],
                        }}
                    >
                        <Close />
                    </IconButton>
                </DialogTitle>
                <DialogContent dividers>
                    <Stack spacing={2.5}>
                        <Typography id="demo-mode-dialog-introduction">
                            {t("demoMode.introduction")}
                        </Typography>

                        <Paper variant="outlined" sx={{ p: 2 }}>
                            <Typography
                                component="h3"
                                variant="subtitle1"
                                sx={{ fontWeight: "bold", mb: 0.5 }}
                            >
                                {t("demoMode.capabilities.title")}
                            </Typography>
                            <List dense disablePadding>
                                {capabilities.map((capability) => (
                                    <ListItem
                                        key={capability}
                                        disableGutters
                                        alignItems="flex-start"
                                    >
                                        <ListItemIcon
                                            sx={{
                                                color: "success.main",
                                                minWidth: 32,
                                                mt: 0.5,
                                            }}
                                        >
                                            <CheckCircleOutlined
                                                fontSize="small"
                                                aria-hidden="true"
                                            />
                                        </ListItemIcon>
                                        <ListItemText primary={capability} />
                                    </ListItem>
                                ))}
                            </List>
                        </Paper>

                        <Alert
                            severity="info"
                            variant="outlined"
                            icon={<InfoOutlined aria-hidden="true" />}
                        >
                            <AlertTitle>
                                {t("demoMode.limitations.title")}
                            </AlertTitle>
                            <Stack spacing={1}>
                                <Typography variant="body2">
                                    {t("demoMode.limitations.backend")}
                                </Typography>
                                <Typography variant="body2">
                                    {t("demoMode.limitations.reset")}
                                </Typography>
                            </Stack>
                        </Alert>
                    </Stack>
                </DialogContent>
                <DialogActions
                    sx={{
                        alignItems: { xs: "stretch", sm: "center" },
                        flexDirection: { xs: "column", sm: "row" },
                        gap: 1.5,
                        justifyContent: "space-between",
                        px: 3,
                        py: 2,
                    }}
                >
                    <Stack spacing={0.5}>
                        <Typography variant="body2" color="text.secondary">
                            {t("demoMode.repository.prompt")}
                        </Typography>
                        <Link
                            href={t("about.link")}
                            target="_blank"
                            rel="noopener noreferrer"
                            variant="body2"
                        >
                            {t("about.link")}
                        </Link>
                    </Stack>
                    <Button
                        variant="contained"
                        onClick={handleClose}
                        sx={{ flex: "0 0 auto" }}
                        startIcon={<RocketLaunch />}
                    >
                        {t("demoMode.startExploring")}
                    </Button>
                </DialogActions>
            </Dialog>
        </>
    );
};
