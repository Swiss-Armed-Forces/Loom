import { Box, Tab, Tabs } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { GetFilePreviewResponse } from "@app/api";
import { SummaryTab } from "@features/common/utils/enums";

import styles from "./Summary.module.css";

interface SummaryProps {
    filePreview: GetFilePreviewResponse;
}

export const Summary = ({ filePreview }: SummaryProps) => {
    const { t } = useTranslation();

    const hasSummary = !!filePreview.summary?.length;
    const hasImageDescription = !!filePreview.imageDescription?.length;

    const [tab, setTab] = useState<SummaryTab>(
        hasSummary ? SummaryTab.Summary : SummaryTab.ImageDescription,
    );

    if (!hasSummary && !hasImageDescription) return null;

    return (
        <Box className={styles.summaryContainer}>
            <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
                <Tabs value={tab} onChange={(_, v) => setTab(v)}>
                    <Tab
                        label={t("generalSearchView.summary")}
                        value={SummaryTab.Summary}
                        disabled={!hasSummary}
                    />
                    <Tab
                        label={t("generalSearchView.imageDescription")}
                        value={SummaryTab.ImageDescription}
                        disabled={!hasImageDescription}
                    />
                </Tabs>
            </Box>
            <Box className={styles.summaryContent}>
                {renderTabContent(tab, filePreview)}
            </Box>
        </Box>
    );
};

const renderTabContent = (
    tab: SummaryTab,
    filePreview: GetFilePreviewResponse,
) => {
    switch (tab) {
        case SummaryTab.Summary:
            return filePreview.summary;
        case SummaryTab.ImageDescription:
            return filePreview.imageDescription;
        default:
            return null;
    }
};
