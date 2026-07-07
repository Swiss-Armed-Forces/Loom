import { Close } from "@mui/icons-material";
import { Box, IconButton, Skeleton, Tab, Tabs } from "@mui/material";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import AceEditorImport from "react-ace";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import {
    GetFileResponse,
    MessageFileUpdate,
    getFile,
    getShortRunningQuery,
    scheduleSingleFileIndexing,
    scheduleSingleFileSummarization,
    scheduleSingleFileTranslation,
    scheduleSingleImageDescription,
    updateFile,
} from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import { setLastFileDetailTab } from "@app/slices/commonSlice";
import {
    closeFileTabThunk,
    fetchPreview,
    selectAutoActionsPreferences,
    selectFileById,
    selectWebSocketPubSubMessage,
    setFilePreview,
    setFileTabDetailTab,
} from "@app/slices/searchSlice";
import { FileRenderer } from "@features/common/components/DialogContainer/Dialogs/FileDetailDialog/FileRenderer";
import { FileTranslations } from "@features/common/components/DialogContainer/Dialogs/FileDetailDialog/FileTranslations";
import { FileDetailTab } from "@features/common/utils/enums";
import { inferAceModeFromMimeType } from "@features/common/utils/helpers";
import { FileCardHeader, HighlightList } from "@features/search/components";

import "ace-builds/esm-resolver";

const AceEditor = (AceEditorImport as any).default ?? AceEditorImport;

interface FileDetailPanelProps {
    fileId: string;
    detailTab: FileDetailTab;
    isActive: boolean;
}

export const FileDetailPanel = ({
    fileId,
    detailTab,
    isActive,
}: FileDetailPanelProps) => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();
    const editorRef = useRef<InstanceType<typeof AceEditorImport>>(null);
    const hasAutoActionsRun = useRef<boolean>(false);
    const lastFetchedFileId = useRef<string>("");

    const [file, setFile] = useState<GetFileResponse>();
    const fetchCancelledRef = useRef(false);

    const autoActionsPreferences = useAppSelector(selectAutoActionsPreferences);
    const webSocketPubSubMessage = useAppSelector(selectWebSocketPubSubMessage);
    const fileData = useAppSelector(selectFileById(fileId));
    const preview = fileData?.preview ?? null;
    const query = fileData?.query ?? null;

    const fetchFileContent = useCallback(async () => {
        if (!query || !preview) return;
        fetchCancelledRef.current = false;
        try {
            const response = await getFile(preview.fileId, {
                ...query,
                id: (await getShortRunningQuery()).queryId,
            });
            if (!fetchCancelledRef.current) setFile(response);
        } catch (error) {
            if (!fetchCancelledRef.current)
                toast.error(
                    `Error loading file: ${error instanceof Error ? error.message : "Unknown error"}`,
                );
        }
    }, [preview, query]);

    // Initial load
    useEffect(() => {
        if (lastFetchedFileId.current === fileId) return;
        dispatch(fetchPreview({ fileId, query: query ?? undefined }));
        lastFetchedFileId.current = fileId;
    }, [fileId]); // eslint-disable-line react-hooks/exhaustive-deps

    // Reset the auto-actions guard when the tab becomes active or preferences
    // change so actions re-run on each navigation to this tab.
    useEffect(() => {
        if (isActive) hasAutoActionsRun.current = false;
    }, [isActive]);

    useEffect(() => {
        hasAutoActionsRun.current = false;
    }, [autoActionsPreferences]);

    // Auto-actions on open / tab activation
    useEffect(() => {
        if (!isActive || !preview || hasAutoActionsRun.current) return;
        hasAutoActionsRun.current = true;

        const prefs = autoActionsPreferences;
        const optimisticUpdates: Partial<typeof preview> = {};

        if (prefs.markAsSeen && !preview.seen) {
            updateFile(fileId, { seen: true }).catch((err) =>
                toast.error(
                    t("updateFileState.seen.scheduledErrorToast", { err }),
                ),
            );
            optimisticUpdates.seen = true;
        }

        if (prefs.flag && !preview.flagged) {
            updateFile(fileId, { flagged: true }).catch((err) =>
                toast.error(
                    t("updateFileState.flagged.scheduledErrorToast", { err }),
                ),
            );
            optimisticUpdates.flagged = true;
        }

        if (Object.keys(optimisticUpdates).length > 0) {
            dispatch(setFilePreview({ ...preview, ...optimisticUpdates }));
        }

        if (prefs.reindex) scheduleSingleFileIndexing(fileId).catch(() => {});
        if (prefs.summarize)
            scheduleSingleFileSummarization(fileId, null).catch(() => {});
        if (prefs.describeImage)
            scheduleSingleImageDescription(fileId, null).catch(() => {});
        if (prefs.translate)
            scheduleSingleFileTranslation("", fileId).catch(() => {});
    }, [isActive, fileId, preview, autoActionsPreferences, dispatch, t]);

    // Content fetch
    useEffect(() => {
        if (!query || !preview) return;
        fetchFileContent();
        return () => {
            fetchCancelledRef.current = true;
        };
    }, [query, preview, fetchFileContent]);

    // WebSocket file updates
    useEffect(() => {
        if (webSocketPubSubMessage?.message.type === "fileUpdate") {
            const message = webSocketPubSubMessage.message as MessageFileUpdate;
            if (message.fileId === fileId) {
                dispatch(fetchPreview({ fileId, query: query ?? undefined }));
                fetchFileContent();
            }
        }
    }, [webSocketPubSubMessage, fileId, query, fetchFileContent]); // eslint-disable-line react-hooks/exhaustive-deps

    const setTab = (value: FileDetailTab) => {
        dispatch(setFileTabDetailTab({ fileId, detailTab: value }));
        dispatch(setLastFileDetailTab(value));
    };

    const handleClose = useCallback(() => {
        dispatch(closeFileTabThunk(fileId));
    }, [fileId, dispatch]);

    const properties = useMemo(
        () => ({
            hasContent: !!file?.content?.trim(),
            hasHighlights:
                !!file?.highlight && Object.keys(file.highlight).length > 0,
            hasSummary: !!file?.summary?.trim(),
            hasImageDescription: !!file?.imageDescription?.trim(),
            hasTranslations: (file?.languageTranslations?.length ?? 0) > 0,
        }),
        [file],
    );

    const formattedRaw = useMemo(
        () =>
            file?.raw
                ? JSON.stringify(JSON.parse(file.raw), null, 2)
                : undefined,
        [file?.raw],
    );

    if (!fileId) return null;

    return (
        <Box
            data-file-panel={fileId}
            sx={{
                display: "flex",
                flexDirection: "column",
                height: "100%",
                overflow: "hidden",
            }}
        >
            {/* File header */}
            <Box
                sx={{
                    flexShrink: 0,
                    borderBottom: 1,
                    borderColor: "divider",
                    px: 1,
                    py: 0.5,
                }}
            >
                {preview ? (
                    <FileCardHeader
                        hideDetail
                        filePreview={preview}
                        additionalActions={[
                            <IconButton
                                key="close"
                                aria-label="close"
                                size="small"
                                onClick={handleClose}
                                title={t("common.close")}
                            >
                                <Close fontSize="small" />
                            </IconButton>,
                        ]}
                    />
                ) : (
                    <Skeleton
                        variant="rectangular"
                        sx={{ width: "100%", height: 48 }}
                    />
                )}
            </Box>

            {/* Inner content tabs */}
            <Box
                sx={{ borderBottom: 1, borderColor: "divider", flexShrink: 0 }}
            >
                <Tabs value={detailTab} onChange={(_, v) => setTab(v)}>
                    <Tab
                        label="Rendered"
                        value={FileDetailTab.Rendered}
                        data-tab-value={FileDetailTab.Rendered}
                    />
                    <Tab
                        label="Content"
                        value={FileDetailTab.Content}
                        data-tab-value={FileDetailTab.Content}
                        disabled={!properties.hasContent}
                    />
                    <Tab
                        label="Highlights"
                        value={FileDetailTab.Highlights}
                        data-tab-value={FileDetailTab.Highlights}
                        disabled={!properties.hasHighlights}
                    />
                    <Tab
                        label="Summary"
                        value={FileDetailTab.Summary}
                        data-tab-value={FileDetailTab.Summary}
                        disabled={!properties.hasSummary}
                    />
                    <Tab
                        label="Image Description"
                        value={FileDetailTab.ImageDescription}
                        data-tab-value={FileDetailTab.ImageDescription}
                        disabled={!properties.hasImageDescription}
                    />
                    <Tab
                        label="Translations"
                        value={FileDetailTab.Translations}
                        data-tab-value={FileDetailTab.Translations}
                        disabled={!properties.hasTranslations}
                    />
                    <Tab
                        label="Raw"
                        value={FileDetailTab.RAW}
                        data-tab-value={FileDetailTab.RAW}
                    />
                </Tabs>
            </Box>

            {/* Content area */}
            <Box
                className="file-panel-content"
                sx={{
                    flex: 1,
                    display: "flex",
                    flexDirection: "column",
                    overflow: "hidden",
                    mt: 1,
                }}
            >
                {!preview || !file ? (
                    <FileSkeleton />
                ) : (
                    renderTabContent(detailTab, file, editorRef, formattedRaw)
                )}
            </Box>
        </Box>
    );
};

const FileSkeleton = () => (
    <Box sx={{ p: 2 }}>
        {[...Array(6)].map((_, i) => (
            <Skeleton key={i} variant="text" sx={{ fontSize: "1rem" }} />
        ))}
    </Box>
);

const renderTabContent = (
    tab: FileDetailTab,
    file: GetFileResponse,
    ref: React.RefObject<InstanceType<typeof AceEditorImport> | null>,
    formattedRaw: string | undefined,
) => {
    const aceProps = {
        ref,
        width: "100%",
        height: "100%",
        readOnly: true,
        theme: "github",
        setOptions: { useWorker: false },
        editorProps: { $blockScrolling: true },
    };

    switch (tab) {
        case FileDetailTab.Content:
            return (
                <AceEditor
                    mode={inferAceModeFromMimeType(file.type)}
                    value={file.content}
                    {...aceProps}
                    wrapEnabled
                />
            );
        case FileDetailTab.Highlights:
            return (
                <Box sx={{ overflow: "auto", flex: 1 }}>
                    <HighlightList
                        highlights={
                            (file.highlight as Record<string, string[]>) ?? {}
                        }
                        fullDetails
                    />
                </Box>
            );
        case FileDetailTab.RAW:
            return (
                <AceEditor
                    mode="json"
                    value={formattedRaw ?? ""}
                    {...aceProps}
                />
            );
        case FileDetailTab.Summary:
            return (
                <AceEditor
                    mode={inferAceModeFromMimeType(file.type)}
                    value={file.summary ?? ""}
                    {...aceProps}
                    wrapEnabled
                />
            );
        case FileDetailTab.ImageDescription:
            return (
                <AceEditor
                    mode="text"
                    value={file.imageDescription ?? ""}
                    {...aceProps}
                    wrapEnabled
                />
            );
        case FileDetailTab.Translations:
            return (
                <FileTranslations
                    translations={file.languageTranslations ?? []}
                />
            );
        case FileDetailTab.Rendered:
        default:
            return (
                <FileRenderer
                    fileId={file.fileId}
                    renderedFile={file.renderedFile}
                    imap={file.imap}
                />
            );
    }
};
