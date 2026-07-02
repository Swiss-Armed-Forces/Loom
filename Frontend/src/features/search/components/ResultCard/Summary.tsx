import { Box, Tab, Tabs } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { GetFilePreviewResponse } from "@app/api";
import { FileDetailTab, SummaryTab } from "@features/common/utils/enums";

import { EllipsisButton } from "./EllipsisButton";
import styles from "./Summary.module.css";

interface SummaryProps {
    filePreview: GetFilePreviewResponse;
    onOpenDetailsTab: (tab: FileDetailTab) => void;
}

export const Summary = ({ filePreview, onOpenDetailsTab }: SummaryProps) => {
    const { t } = useTranslation();

    const hasContent = !!filePreview.content?.length;
    const hasSummary = !!filePreview.summary?.length;
    const hasImageDescription = !!filePreview.imageDescription?.length;
    const hasTranslation = !!filePreview.translationPreview?.length;

    const [tab, setTab] = useState<SummaryTab>(SummaryTab.Content);

    if (!hasContent && !hasSummary && !hasImageDescription && !hasTranslation)
        return null;

    return (
        <Box className={styles.summaryContainer}>
            <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
                <Tabs
                    value={tab}
                    onChange={(_, v) => setTab(v)}
                    sx={{ minHeight: 0 }}
                >
                    <Tab
                        label={t("generalSearchView.content")}
                        value={SummaryTab.Content}
                        disabled={!hasContent}
                        sx={{ minHeight: 0, py: 0.5, fontSize: "0.75rem" }}
                    />
                    <Tab
                        label={t("generalSearchView.summary")}
                        value={SummaryTab.Summary}
                        disabled={!hasSummary}
                        sx={{ minHeight: 0, py: 0.5, fontSize: "0.75rem" }}
                    />
                    <Tab
                        label={t("generalSearchView.imageDescription")}
                        value={SummaryTab.ImageDescription}
                        disabled={!hasImageDescription}
                        sx={{ minHeight: 0, py: 0.5, fontSize: "0.75rem" }}
                    />
                    <Tab
                        label={t("generalSearchView.translation")}
                        value={SummaryTab.Translation}
                        disabled={!hasTranslation}
                        sx={{ minHeight: 0, py: 0.5, fontSize: "0.75rem" }}
                    />
                </Tabs>
            </Box>
            <Box className={styles.summaryContent}>
                {renderTabContent(tab, filePreview, onOpenDetailsTab, t)}
            </Box>
        </Box>
    );
};

const renderTabContent = (
    tab: SummaryTab,
    filePreview: GetFilePreviewResponse,
    onOpenDetailsTab: (tab: FileDetailTab) => void,
    t: (key: string) => string,
) => {
    switch (tab) {
        case SummaryTab.Content:
            return (
                <>
                    {filePreview.content}
                    {filePreview.contentPreviewIsTruncated && (
                        <EllipsisButton
                            onClick={() =>
                                onOpenDetailsTab(FileDetailTab.Content)
                            }
                            title={t("generalSearchView.viewDetails")}
                        />
                    )}
                </>
            );
        case SummaryTab.Summary:
            return filePreview.summary;
        case SummaryTab.ImageDescription:
            return filePreview.imageDescription;
        case SummaryTab.Translation:
            return (
                <>
                    {filePreview.translationPreview}
                    {filePreview.translationPreviewIsTruncated && (
                        <EllipsisButton
                            onClick={() =>
                                onOpenDetailsTab(FileDetailTab.Translations)
                            }
                            title={t("generalSearchView.viewDetails")}
                        />
                    )}
                </>
            );
        default:
            return null;
    }
};
