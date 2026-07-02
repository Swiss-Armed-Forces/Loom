import { Close, Download } from "@mui/icons-material";
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
} from "@mui/material";
import Ajv, { JSONSchemaType } from "ajv";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { DialogProps } from "@app/slices/commonSlice";

const AJV = new Ajv();

export interface HelmChartMetadata {
    apiVersion: string;
    appVersion: string;
    description: string;
    name: string;
    version: string;
}

const HelmChartMetadataSchema: JSONSchemaType<HelmChartMetadata> = {
    type: "object",
    properties: {
        apiVersion: { type: "string" },
        appVersion: { type: "string" },
        description: { type: "string" },
        name: { type: "string" },
        version: { type: "string" },
    },
    required: ["apiVersion", "appVersion", "description", "name", "version"],
    additionalProperties: false,
};

const loadHelmChartMetadata = (chartData: string): HelmChartMetadata | null => {
    const parsed = JSON.parse(chartData);

    const validate = AJV.compile(HelmChartMetadataSchema);

    if (validate(parsed)) {
        return parsed;
    } else {
        console.warn("Invalid Helm chart metadata:", validate.errors);
        return null;
    }
};

export const AboutDialog = ({ onClose, isTop }: DialogProps) => {
    const [licenseText, setLicenseText] = useState<string>("");
    const [helmChartMetadata, setHelmChartMetadata] =
        useState<HelmChartMetadata | null>(null);
    const { t } = useTranslation();

    useEffect(() => {
        const fetchLicense = async () => {
            const license = await fetch("/" + t("about.license"));
            setLicenseText(await license.text());
        };
        const fetchChartData = async () => {
            const chartData = await fetch("/" + t("about.chartData"));
            setHelmChartMetadata(loadHelmChartMetadata(await chartData.text()));
        };

        fetchLicense();
        fetchChartData();
    }, [t]);

    return (
        <Dialog
            maxWidth="md"
            open
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
                            {helmChartMetadata?.name} v
                            {helmChartMetadata?.appVersion}
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
                            {helmChartMetadata?.description}
                        </Typography>
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
                                bgcolor: "grey.50",
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
                        <Stack direction="row" spacing={2}>
                            <Button
                                variant="outlined"
                                size="small"
                                href={"/" + t("about.license")}
                                download
                                startIcon={<Download />}
                            >
                                {t("about.license")}
                            </Button>
                            <Button
                                variant="outlined"
                                size="small"
                                href={"/" + t("about.thirdParty")}
                                download
                                startIcon={<Download />}
                            >
                                {t("about.thirdParty")}
                            </Button>
                        </Stack>
                    </Box>
                </Stack>
            </DialogContent>
        </Dialog>
    );
};
