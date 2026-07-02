import { Close, Fullscreen, FullscreenExit } from "@mui/icons-material";
import {
    Dialog,
    DialogContent,
    DialogTitle,
    Skeleton,
    Tabs,
    Tab,
    Box,
    IconButton,
} from "@mui/material";
import { useEffect, useState, useRef, useCallback, useMemo } from "react";
import AceEditorImport from "react-ace";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import {
    GetFileResponse,
    MessageFileUpdate,
    getFile,
    getShortRunningQuery,
    updateFile,
} from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    DialogProps,
    setLastFileDetailTab,
    startLoadingIndicator,
    stopLoadingIndicator,
    updateDialogPropsById,
} from "@app/slices/commonSlice";
import {
    fetchPreview,
    selectFileById,
    selectWebSocketPubSubMessage,
    setFilePreview,
} from "@app/slices/searchSlice";
import { FileDetailTab } from "@features/common/utils/enums";
import { inferAceModeFromMimeType } from "@features/common/utils/helpers";
import { FileCardHeader, HighlightList } from "@features/search/components";

import { FileRenderer } from "./FileRenderer";
import { FileTranslations } from "./FileTranslations";

import "ace-builds/esm-resolver";

const AceEditor = (AceEditorImport as any).default ?? AceEditorImport;

interface FileDetailDialogProps extends DialogProps {
    fileId: string;
    tab: FileDetailTab;
}

export const FileDetailDialog = ({
    id,
    fileId,
    tab = FileDetailTab.Rendered,
    onClose,
}: FileDetailDialogProps) => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();
    const editorRef = useRef<InstanceType<typeof AceEditorImport>>(null);
    const hasUpdatedSeen = useRef<boolean>(false);

    const [file, setFile] = useState<GetFileResponse>();
    const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
    const lastFetchedFileId = useRef<string>("");

    const webSocketPubSubMessage = useAppSelector(selectWebSocketPubSubMessage);
    const fileData = useAppSelector(selectFileById(fileId));
    const preview = fileData?.preview ?? null;
    const query = fileData?.query ?? null;

    const fetchFileContent = useCallback(async () => {
        if (!query || !preview) return;

        try {
            const response = await getFile(preview.fileId, {
                ...query,
                id: (await getShortRunningQuery()).queryId,
            });
            setFile(response);
        } catch (error) {
            toast.error(
                `Error loading file: ${error instanceof Error ? error.message : "Unknown error"}`,
            );
        }
    }, [preview, query]);

    // Initial Load & Preview Fetch
    useEffect(() => {
        if (lastFetchedFileId.current === fileId) return;
        dispatch(fetchPreview({ fileId, query: query ?? undefined }));
        lastFetchedFileId.current = fileId;

        if (window.location.hash.substring(1) !== fileId) {
            window.history.pushState(
                null,
                "",
                `${window.location.pathname}${window.location.search}#${fileId}`,
            );
        }
    }, [fileId]); // eslint-disable-line react-hooks/exhaustive-deps

    // Mark File as Seen
    useEffect(() => {
        if (preview && !preview.seen && !hasUpdatedSeen.current) {
            updateFile(fileId, { seen: true })
                .then(() => {
                    hasUpdatedSeen.current = true;
                    dispatch(setFilePreview({ ...preview, seen: true }));
                })
                .catch((err) =>
                    toast.error(
                        t("updateFileState.seen.scheduledErrorToast", { err }),
                    ),
                );
        }
    }, [fileId, preview]); // eslint-disable-line react-hooks/exhaustive-deps

    // Content Fetch with Loading Indicator
    useEffect(() => {
        if (!query || !preview) return;

        const load = async () => {
            dispatch(startLoadingIndicator());
            await fetchFileContent();
            dispatch(stopLoadingIndicator());
        };
        load();
    }, [query, preview, fetchFileContent]); // eslint-disable-line react-hooks/exhaustive-deps

    // Consolidated WebSocket Listener
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
        dispatch(updateDialogPropsById({ id, props: { tab: value } }));
        dispatch(setLastFileDetailTab(value));
    };

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

    const handleClose = useCallback(() => {
        const fileIdInPath = window.location.hash.substring(1);
        if (fileIdInPath === fileId) {
            window.history.pushState(
                null,
                "",
                window.location.pathname + window.location.search,
            );
        }
        onClose();
    }, [fileId, onClose]);

    if (!fileId) return null;

    return (
        <Dialog
            id={`file-detail-${id}`}
            open
            onClose={handleClose}
            maxWidth="xl"
            fullWidth
            fullScreen={isFullscreen}
            slotProps={{
                paper: { sx: { ...(!isFullscreen && { height: "80vh" }) } },
            }}
        >
            <DialogTitle
                sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 2,
                    p: 2,
                    pb: 1,
                }}
            >
                {preview ? (
                    <FileCardHeader
                        hideDetail={true}
                        filePreview={preview}
                        additionalActions={[
                            <IconButton
                                key="fs"
                                title={
                                    isFullscreen
                                        ? "Exit Fullscreen"
                                        : "Fullscreen"
                                }
                                onClick={() => setIsFullscreen(!isFullscreen)}
                            >
                                {isFullscreen ? (
                                    <FullscreenExit />
                                ) : (
                                    <Fullscreen />
                                )}
                            </IconButton>,
                            <IconButton
                                key="close"
                                aria-label="close"
                                onClick={handleClose}
                                title={t("common.close")}
                            >
                                <Close />
                            </IconButton>,
                        ]}
                    />
                ) : (
                    <Skeleton variant="rectangular" sx={{ width: "100%" }} />
                )}
            </DialogTitle>

            <DialogContent sx={{ display: "flex", flexDirection: "column" }}>
                <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
                    <Tabs value={tab} onChange={(_, v) => setTab(v)}>
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
                            label="Raw"
                            value={FileDetailTab.RAW}
                            data-tab-value={FileDetailTab.RAW}
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
                            disabled={!properties.hasImageDescription}
                        />
                        <Tab
                            label="Translations"
                            value={FileDetailTab.Translations}
                            data-tab-value={FileDetailTab.Translations}
                            disabled={!properties.hasTranslations}
                        />
                    </Tabs>
                </Box>

                <Box
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
                        renderTabContent(tab, file, editorRef)
                    )}
                </Box>
            </DialogContent>
        </Dialog>
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
                    value={JSON.stringify(JSON.parse(file.raw), null, 2)}
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
