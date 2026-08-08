import {
    ArticleOutlined,
    AssignmentOutlined,
    CodeOutlined,
    FormatColorTextOutlined,
    ImageOutlined,
    ShortTextOutlined,
    TranslateOutlined,
    VisibilityOutlined,
} from "@mui/icons-material";
import { Box, Skeleton, Tab, Tabs } from "@mui/material";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import AceEditorImport from "react-ace";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import {
    GetFileResponse,
    MessageFileUpdate,
    getFile,
    scheduleSingleFileIndexing,
    scheduleSingleFileSummarization,
    scheduleSingleFileTranslation,
    scheduleSingleImageDescription,
    updateFile,
} from "@app/api";
import {
    subscribeChannel,
    unsubscribeChannel,
} from "@app/channelSubscriptions";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import { setLastFileDetailTab } from "@app/slices/commonSlice";
import {
    fetchPreview,
    selectAutoActionsPreferences,
    selectFileById,
    selectQuery,
    selectWebSocketPubSubMessage,
    setFilePreview,
    setFileTabDetailTab,
} from "@app/slices/searchSlice";
import { FileRenderer } from "@features/common/components/DialogContainer/Dialogs/FileDetailDialog/FileRenderer";
import { FileTasks } from "@features/common/components/DialogContainer/Dialogs/FileDetailDialog/FileTasks";
import { FileTranslations } from "@features/common/components/DialogContainer/Dialogs/FileDetailDialog/FileTranslations";
import { useDarkMode } from "@features/common/hooks/useDarkMode";
import { FileDetailTab } from "@features/common/utils/enums";
import { inferAceModeFromMimeType } from "@features/common/utils/helpers";
import { FileCardHeader, FieldList } from "@features/search/components";

import "ace-builds/esm-resolver";

const AceEditor = (AceEditorImport as any).default ?? AceEditorImport;

interface FileDetailPanelProps {
    fileId: string;
    detailTab: FileDetailTab;
    isActive: boolean;
    compact?: boolean;
}

export const FileDetailPanel = ({
    fileId,
    detailTab,
    isActive,
    compact,
}: FileDetailPanelProps) => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();
    const editorRef = useRef<InstanceType<typeof AceEditorImport>>(null);
    const hasAutoActionsRun = useRef<boolean>(false);
    const lastFetchedFileId = useRef<string>("");
    const panelRef = useRef<HTMLDivElement>(null);
    const [panelWidth, setPanelWidth] = useState(Infinity);
    const isDarkMode = useDarkMode();

    useEffect(() => {
        const el = panelRef.current;
        if (!el) return;
        const ro = new ResizeObserver(([entry]) =>
            setPanelWidth(entry.contentRect.width),
        );
        ro.observe(el);
        return () => ro.disconnect();
    }, []);

    const isNarrow = panelWidth < 500;

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
                id: null,
            });
            if (!fetchCancelledRef.current) setFile(response);
        } catch (error) {
            if (!fetchCancelledRef.current)
                toast.error(
                    `Error loading file: ${error instanceof Error ? error.message : "Unknown error"}`,
                );
        }
    }, [preview, query]);

    // Subscribe to WS updates for this file while the panel is mounted.
    // All panels are always mounted (just hidden when inactive), so this covers
    // background tabs that are restored from localStorage on page reload but
    // were not re-subscribed by openFileTabThunk (which only runs for the
    // active tab via the URL→Redux hash effect). The ref-counted channel
    // subscription system handles the overlap with openFileTabThunk safely.
    useEffect(() => {
        subscribeChannel(fileId, dispatch);
        return () => unsubscribeChannel(fileId, dispatch);
    }, [fileId, dispatch]);

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

    // Stable refs so the WS effect can always read the latest values without
    // listing them as deps. Putting fetchFileContent or query in deps would
    // cause an infinite loop: fetchPreview stores a new query object reference
    // into the Redux store, which changes `query`, which re-triggers the WS
    // effect with the same stale message — repeating indefinitely.
    const fetchFileContentRef = useRef(fetchFileContent);
    const queryRef = useRef(query);
    useEffect(() => {
        fetchFileContentRef.current = fetchFileContent;
        queryRef.current = query;
    });

    // WebSocket file updates
    useEffect(() => {
        if (webSocketPubSubMessage?.message.type === "fileUpdate") {
            const message = webSocketPubSubMessage.message as MessageFileUpdate;
            if (message.fileId === fileId) {
                dispatch(
                    fetchPreview({
                        fileId,
                        query: queryRef.current ?? undefined,
                    }),
                );
                fetchFileContentRef.current();
            }
        }
    }, [webSocketPubSubMessage, fileId, dispatch]);

    // Re-fetch when the global search query string changes so highlights stay
    // in sync. Uses the query string (not the full query object) to ignore
    // keep-alive ID renewals that don't change the actual search.
    const searchQueryString = useAppSelector(
        (state) => selectQuery(state)?.query ?? null,
    );
    const prevSearchQueryStringRef = useRef(searchQueryString);
    useEffect(() => {
        if (searchQueryString === prevSearchQueryStringRef.current) return;
        prevSearchQueryStringRef.current = searchQueryString;
        dispatch(fetchPreview({ fileId }));
    }, [searchQueryString, fileId, dispatch]);

    const setTab = (value: FileDetailTab) => {
        dispatch(setFileTabDetailTab({ fileId, detailTab: value }));
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

    const formattedRaw = useMemo(() => {
        if (!file?.raw) return undefined;
        try {
            return JSON.stringify(JSON.parse(file.raw), null, 2);
        } catch {
            return file.raw;
        }
    }, [file?.raw]);

    if (!fileId) return null;

    return (
        <Box
            ref={panelRef}
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
                        compact={compact}
                        filePreview={preview}
                        renderedFile={file?.renderedFile}
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
                <Tabs
                    value={detailTab}
                    onChange={(_, v) => setTab(v)}
                    variant="scrollable"
                    scrollButtons="auto"
                >
                    {[
                        {
                            label: "Rendered",
                            value: FileDetailTab.Rendered,
                            icon: <VisibilityOutlined fontSize="small" />,
                        },
                        {
                            label: "Content",
                            value: FileDetailTab.Content,
                            icon: <ArticleOutlined fontSize="small" />,
                            disabled: !properties.hasContent,
                        },
                        {
                            label: "Translations",
                            value: FileDetailTab.Translations,
                            icon: <TranslateOutlined fontSize="small" />,
                            disabled: !properties.hasTranslations,
                            dataTour: "detail-translations",
                        },
                        {
                            label: "Highlights",
                            value: FileDetailTab.Highlights,
                            icon: <FormatColorTextOutlined fontSize="small" />,
                            disabled: !properties.hasHighlights,
                            dataTour: "detail-highlights",
                        },
                        {
                            label: "Summary",
                            value: FileDetailTab.Summary,
                            icon: <ShortTextOutlined fontSize="small" />,
                            disabled: !properties.hasSummary,
                        },
                        {
                            label: "Image",
                            value: FileDetailTab.ImageDescription,
                            icon: <ImageOutlined fontSize="small" />,
                            disabled: !properties.hasImageDescription,
                        },
                        {
                            label: "Raw",
                            value: FileDetailTab.RAW,
                            icon: <CodeOutlined fontSize="small" />,
                            dataTour: "detail-raw",
                        },
                        {
                            label: "Tasks",
                            value: FileDetailTab.Tasks,
                            icon: <AssignmentOutlined fontSize="small" />,
                        },
                    ].map(({ label, value, icon, disabled, dataTour }) => (
                        <Tab
                            key={value}
                            icon={icon}
                            iconPosition="start"
                            label={isNarrow ? undefined : label}
                            title={isNarrow ? label : undefined}
                            value={value}
                            data-tab-value={value}
                            data-tour={dataTour}
                            disabled={disabled}
                            sx={
                                isNarrow
                                    ? { minWidth: "auto", px: 1.5 }
                                    : undefined
                            }
                        />
                    ))}
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
                    renderTabContent(
                        detailTab,
                        file,
                        editorRef,
                        formattedRaw,
                        isDarkMode,
                    )
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
    isDarkMode: boolean,
) => {
    const aceProps = {
        ref,
        width: "100%",
        height: "100%",
        readOnly: true,
        theme: isDarkMode ? "tomorrow_night" : "github",
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
                    <FieldList
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
        case FileDetailTab.Tasks:
            return (
                <Box sx={{ overflow: "auto", flex: 1 }}>
                    <FileTasks tasks={file.tasks} />
                </Box>
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
