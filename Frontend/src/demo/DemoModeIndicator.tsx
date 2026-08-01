import {
    Close,
    InfoOutlined,
    RocketLaunch,
    ScienceOutlined,
    TourOutlined,
} from "@mui/icons-material";
import {
    Alert,
    Box,
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Divider,
    IconButton,
    Link,
    Stack,
    Typography,
} from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate } from "react-router-dom";

import { startWhenDialogsClose } from "@app/tours/startWhenDialogsClose";
import { useTour } from "@app/tours/useTour";

import styles from "./DemoModeIndicator.module.css";

export const DemoModeIndicator = () => {
    const [open, setOpen] = useState(true);
    const { t } = useTranslation();
    const location = useLocation();
    const navigate = useNavigate();
    const { startTour } = useTour();

    const handleClose = () => {
        setOpen(false);
    };

    const handleTourClick = () => {
        if (location.pathname !== "/search") navigate("/search");
        startWhenDialogsClose(startTour);
        handleClose();
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
                maxWidth="xs"
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
                                height: 36,
                                justifyContent: "center",
                                width: 36,
                            }}
                        >
                            <ScienceOutlined
                                aria-hidden="true"
                                fontSize="small"
                            />
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
                <DialogContent sx={{ pt: 2 }}>
                    <Stack spacing={2} divider={<Divider />}>
                        <Stack spacing={1.5}>
                            <Typography
                                variant="body2"
                                id="demo-mode-dialog-introduction"
                            >
                                {t("demoMode.introduction")}
                            </Typography>
                            <Alert
                                severity="info"
                                variant="outlined"
                                icon={<InfoOutlined aria-hidden="true" />}
                            >
                                <Typography variant="body2">
                                    {t("demoMode.limitations")}
                                </Typography>
                            </Alert>
                        </Stack>
                        <Box>
                            <Typography
                                component="h3"
                                variant="subtitle2"
                                sx={{ fontWeight: "bold", mb: 0.5 }}
                            >
                                {t("demoMode.tour.title")}
                            </Typography>
                            <Typography variant="body2" sx={{ mb: 1.5 }}>
                                {t("demoMode.tour.description")}
                            </Typography>
                            <Button
                                variant="contained"
                                startIcon={<TourOutlined />}
                                onClick={handleTourClick}
                            >
                                {t("tour.takeTour")}
                            </Button>
                        </Box>
                    </Stack>
                </DialogContent>
                <DialogActions
                    sx={{
                        justifyContent: "space-between",
                        px: 3,
                        py: 2,
                    }}
                >
                    <Link
                        href={t("about.link")}
                        target="_blank"
                        rel="noopener noreferrer"
                        variant="body2"
                    >
                        {t("demoMode.repository.action")}
                    </Link>
                    <Button
                        variant="contained"
                        onClick={handleClose}
                        startIcon={<RocketLaunch />}
                    >
                        {t("demoMode.startExploring")}
                    </Button>
                </DialogActions>
            </Dialog>
        </>
    );
};
