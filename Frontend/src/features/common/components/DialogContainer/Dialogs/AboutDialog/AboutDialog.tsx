import { Close, Download, TourOutlined } from "@mui/icons-material";
import {
    Box,
    Button,
    Dialog,
    DialogContent,
    DialogTitle,
    IconButton,
    Link,
    Paper,
    Stack,
    Typography,
    useMediaQuery,
} from "@mui/material";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate } from "react-router-dom";

import { AboutInfo, fetchAbout } from "@app/api";
import { DialogProps } from "@app/slices/commonSlice";
import { startWhenDialogsClose } from "@app/tours/startWhenDialogsClose";
import { useTour } from "@app/tours/useTour";

const basePath = import.meta.env.BASE_URL;

export const AboutDialog = ({ onClose, isTop }: DialogProps) => {
    const [licenseText, setLicenseText] = useState<string>("");
    const [about, setAbout] = useState<AboutInfo | null>(null);
    const { t } = useTranslation();
    const isMobile = useMediaQuery("(max-width:600px)");
    const location = useLocation();
    const navigate = useNavigate();
    const { startTour } = useTour();

    const handleTourClick = () => {
        if (location.pathname !== "/search") navigate("/search");
        startWhenDialogsClose(startTour);
        onClose();
    };

    useEffect(() => {
        const fetchLicense = async () => {
            const license = await fetch(`${basePath}${t("about.license")}`);
            setLicenseText(await license.text());
        };
        const fetchChartMetadata = async () => {
            setAbout(await fetchAbout());
        };

        fetchLicense();
        fetchChartMetadata();
    }, [t]);

    return (
        <Dialog
            maxWidth="md"
            fullWidth
            open
            fullScreen={isMobile}
            disableEnforceFocus={!isTop}
            onClose={onClose}
        >
            <DialogTitle>
                <Box
                    sx={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                    }}
                >
                    <Box>
                        <Typography
                            variant="h5"
                            component="div"
                            sx={{
                                fontWeight: "bold",
                            }}
                        >
                            {t("about.title")}
                        </Typography>
                        <Typography
                            variant="subtitle1"
                            sx={{
                                color: "text.secondary",
                            }}
                        >
                            {about?.name} v{about?.appVersion}
                        </Typography>
                    </Box>
                    <IconButton
                        aria-label="close"
                        onClick={onClose}
                        title={t("common.close")}
                        sx={{ color: (theme) => theme.palette.grey[500] }}
                    >
                        <Close />
                    </IconButton>
                </Box>
            </DialogTitle>
            <DialogContent dividers>
                <Stack spacing={3}>
                    {/* Description Section */}
                    <Box>
                        <Typography variant="body1" component="p">
                            {about?.description}
                        </Typography>
                    </Box>

                    {/* Tour Section */}
                    <Box>
                        <Button
                            variant="outlined"
                            startIcon={<TourOutlined />}
                            onClick={handleTourClick}
                        >
                            {t("tour.takeTour")}
                        </Button>
                    </Box>

                    {/* Links Section */}
                    <Box>
                        <Typography
                            variant="subtitle2"
                            gutterBottom
                            sx={{
                                fontWeight: "bold",
                            }}
                        >
                            {t("about.linkTitle")}
                        </Typography>
                        <Link
                            href={t("about.link")}
                            target="_blank"
                            rel="noreferrer"
                            sx={{ display: "block", mb: 1 }}
                        >
                            {t("about.link")}
                        </Link>
                    </Box>

                    {/* License Section */}
                    <Box>
                        <Typography
                            variant="subtitle2"
                            gutterBottom
                            sx={{
                                fontWeight: "bold",
                            }}
                        >
                            License
                        </Typography>
                        <Paper
                            variant="outlined"
                            sx={{
                                p: 2,
                                maxHeight: 200,
                                overflow: "auto",
                                bgcolor: "action.hover",
                            }}
                        >
                            <Typography
                                component="pre"
                                variant="body2"
                                sx={{
                                    fontFamily: "monospace",
                                    whiteSpace: "pre-wrap",
                                    m: 0,
                                }}
                            >
                                {licenseText}
                            </Typography>
                        </Paper>
                    </Box>

                    {/* Downloads Section */}
                    <Box>
                        <Typography
                            variant="subtitle2"
                            gutterBottom
                            sx={{
                                fontWeight: "bold",
                            }}
                        >
                            Downloads
                        </Typography>
                        <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
                            <Button
                                variant="outlined"
                                size="small"
                                href={`${basePath}${t("about.license")}`}
                                download
                                startIcon={<Download />}
                            >
                                License
                            </Button>
                            <Button
                                variant="outlined"
                                size="small"
                                href={`${basePath}${t("about.thirdParty")}`}
                                download
                                startIcon={<Download />}
                            >
                                Third-party
                            </Button>
                            <Button
                                variant="outlined"
                                size="small"
                                href={`${basePath}${t("about.contributing")}`}
                                download
                                startIcon={<Download />}
                            >
                                Contributing
                            </Button>
                            <Button
                                variant="outlined"
                                size="small"
                                href={`${basePath}${t("about.codeOfConduct")}`}
                                download
                                startIcon={<Download />}
                            >
                                Code of Conduct
                            </Button>
                            <Button
                                variant="outlined"
                                size="small"
                                href={`${basePath}demo-link-qr.gif`}
                                download
                                startIcon={<Download />}
                            >
                                QR Code (GIF)
                            </Button>
                            <Button
                                variant="outlined"
                                size="small"
                                href={`${basePath}demo-link-qr.svg`}
                                download
                                startIcon={<Download />}
                            >
                                QR Code (SVG)
                            </Button>
                        </Box>
                    </Box>
                </Stack>
            </DialogContent>
        </Dialog>
    );
};
