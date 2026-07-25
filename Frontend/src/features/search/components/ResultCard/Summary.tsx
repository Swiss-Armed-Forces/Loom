import {
    ArticleOutlined,
    ImageOutlined,
    ShortTextOutlined,
    TranslateOutlined,
} from "@mui/icons-material";
import { Box, Tab, Tabs, useMediaQuery, useTheme } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { GetFilePreviewResponse } from "@app/api";
import { FileDetailTab, SummaryTab } from "@features/common/utils/enums";

import { EllipsisButton } from "./EllipsisButton";

interface SummaryProps {
    filePreview: GetFilePreviewResponse;
    onOpenDetailsTab: (tab: FileDetailTab, background?: boolean) => void;
}

export const Summary = ({ filePreview, onOpenDetailsTab }: SummaryProps) => {
    const { t } = useTranslation();
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

    const hasContent = !!filePreview.content?.length;
    const hasSummary = !!filePreview.summary?.length;
    const hasImageDescription = !!filePreview.imageDescription?.length;
    const hasTranslation = !!filePreview.translationPreview?.length;

    const [tab, setTab] = useState<SummaryTab>(SummaryTab.Content);

    if (!hasContent && !hasSummary && !hasImageDescription && !hasTranslation)
        return null;

    const tabs = [
        {
            label: t("generalSearchView.content"),
            value: SummaryTab.Content,
            icon: <ArticleOutlined fontSize="small" />,
            disabled: !hasContent,
        },
        {
            label: t("generalSearchView.summary"),
            value: SummaryTab.Summary,
            icon: <ShortTextOutlined fontSize="small" />,
            disabled: !hasSummary,
        },
        {
            label: t("generalSearchView.imageDescription"),
            value: SummaryTab.ImageDescription,
            icon: <ImageOutlined fontSize="small" />,
            disabled: !hasImageDescription,
        },
        {
            label: t("generalSearchView.translation"),
            value: SummaryTab.Translation,
            icon: <TranslateOutlined fontSize="small" />,
            disabled: !hasTranslation,
        },
    ];

    return (
        <Box sx={{ bgcolor: "action.hover", borderRadius: 1, p: 1 }}>
            <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
                <Tabs
                    value={tab}
                    onChange={(_, v) => setTab(v)}
                    sx={{ minHeight: 0 }}
                >
                    {tabs.map(({ label, value, icon, disabled }) => (
                        <Tab
                            key={value}
                            icon={icon}
                            iconPosition="start"
                            label={isMobile ? undefined : label}
                            title={isMobile ? label : undefined}
                            value={value}
                            disabled={disabled}
                            sx={{
                                minHeight: 0,
                                py: 0.5,
                                fontSize: "0.75rem",
                                ...(isMobile && { minWidth: "auto", px: 1 }),
                            }}
                        />
                    ))}
                </Tabs>
            </Box>
            <Box sx={{ pt: 1 }}>
                {renderTabContent(tab, filePreview, onOpenDetailsTab, t)}
            </Box>
        </Box>
    );
};

const renderTabContent = (
    tab: SummaryTab,
    filePreview: GetFilePreviewResponse,
    onOpenDetailsTab: (tab: FileDetailTab, background?: boolean) => void,
    t: (key: string) => string,
) => {
    switch (tab) {
        case SummaryTab.Content:
            return (
                <>
                    {filePreview.content}
                    {filePreview.contentPreviewIsTruncated && (
                        <EllipsisButton
                            onClick={(e) =>
                                onOpenDetailsTab(
                                    FileDetailTab.Content,
                                    e.ctrlKey,
                                )
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
                            onClick={(e) =>
                                onOpenDetailsTab(
                                    FileDetailTab.Translations,
                                    e.ctrlKey,
                                )
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
