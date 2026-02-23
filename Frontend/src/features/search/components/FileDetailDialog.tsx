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
import { useEffect, useState, useRef, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useAppDispatch, useAppSelector } from "../../../app/hooks";
import {
    GetFileResponse,
    MessageFileUpdate,
    getFile as getFile,
    getShortRunningQuery,
} from "../../../app/api";
import AceEditor from "react-ace";
import {
    fetchFileDetailData,
    selectFileDetailData,
    selectWebSocketPubSubMessage,
    setFileDetailData,
} from "../searchSlice";
import styles from "./FileDetailDialog.module.css";
import { HighlightList } from "../container/HighlightList";

import { FileDetailTab } from "../model";
import {
    startLoadingIndicator,
    stopLoadingIndicator,
} from "../../common/commonSlice";

import "ace-builds/esm-resolver";
import { FileRenderer } from "./FileRenderer";
import { FileTranslations } from "./FileTranslations";
import { Close, Fullscreen, FullscreenExit } from "@mui/icons-material";
import { FileCardHeader } from "../container/FileCardHeader";
import { toast } from "react-toastify";
import { inferAceModeFromMimeType } from "../../common/inferAceModeFromMimeType";

const FILE_FETCH_DEBOUNCE__MS = 2_000;

export function FileDetailDialog() {
    const webSocketPubSubMessage = useAppSelector(selectWebSocketPubSubMessage);
    const fileDetailData = useAppSelector(selectFileDetailData);
    const dispatch = useAppDispatch();
    const { t } = useTranslation();

    const editorRef = useRef<AceEditor>(null);

    const [file, setFile] = useState<GetFileResponse>();

    const [isFullscreen, setIsFullscreen] = useState(false);

    const fileDetailDataFetchDebounceTimeout = useRef<
        ReturnType<typeof setTimeout> | undefined
    >(undefined);

    const fileFetchDebounceTimeout = useRef<
        ReturnType<typeof setTimeout> | undefined
    >(undefined); // see: https://stackoverflow.com/a/56239226/3215929

    const openDialog = !!(
        fileDetailData.filePreview && fileDetailData.searchQuery
    );

    const openDialogRef = useRef(openDialog);

    // Track current fileId to prevent stale closure race conditions
    const currentFileIdRef = useRef<string | undefined>(undefined);

    // Update ref whenever openDialog changes
    useEffect(() => {
        openDialogRef.current = openDialog;
    }, [openDialog]);

    // Update ref whenever fileId changes
    useEffect(() => {
        currentFileIdRef.current = fileDetailData.filePreview?.fileId;
    }, [fileDetailData.filePreview?.fileId]);

    async function fetchFile() {
        if (!fileDetailData.searchQuery) return;
        if (!fileDetailData.filePreview) return;
        if (!openDialogRef.current) return; // Check current value via ref

        // Capture fileId before async operation to detect stale closure
        const expectedFileId = fileDetailData.filePreview.fileId;

        const response = await getFile(fileDetailData.filePreview.fileId, {
            ...fileDetailData.searchQuery,
            id: (await getShortRunningQuery()).queryId,
        });

        // Only update state if this is still the file we're showing
        // Use ref to get CURRENT fileId, not stale closure value
        if (currentFileIdRef.current !== expectedFileId) {
            return; // Dialog has changed, discard stale response
        }

        setFile(response);
    }

    useEffect(() => {
        if (!fileDetailData.searchQuery) return;
        if (!fileDetailData.filePreview) return;

        async function load() {
            dispatch(startLoadingIndicator());
            try {
                await Promise.all([fetchFile()]);
            } catch (errorPayload: any) {
                toast.error(`Error in load: ${errorPayload}`);
            } finally {
                dispatch(stopLoadingIndicator());
            }
        }
        load();
    }, [fileDetailData.filePreview?.fileId, fileDetailData.searchQuery]); // eslint-disable-line react-hooks/exhaustive-deps

    // fetch file detail on change
    useEffect(() => {
        if (!webSocketPubSubMessage) return;
        if (webSocketPubSubMessage.message.type !== "fileUpdate") return;
        const message = webSocketPubSubMessage.message as MessageFileUpdate;

        const fileId = message.fileId;
        if (fileId !== fileDetailData.filePreview?.fileId) return;
        clearTimeout(fileDetailDataFetchDebounceTimeout.current);
        const newTimeout = setTimeout(() => {
            if (!openDialogRef.current) return; // Check current value via ref
            dispatch(fetchFileDetailData({ fileId }));
        }, FILE_FETCH_DEBOUNCE__MS);
        fileDetailDataFetchDebounceTimeout.current = newTimeout;
    }, [webSocketPubSubMessage]); // eslint-disable-line react-hooks/exhaustive-deps

    // fetch file on change
    useEffect(() => {
        if (!webSocketPubSubMessage) return;
        if (webSocketPubSubMessage.message.type !== "fileUpdate") return;
        const message = webSocketPubSubMessage.message as MessageFileUpdate;

        const fileId = message.fileId;
        if (fileId !== fileDetailData.filePreview?.fileId) return;

        clearTimeout(fileFetchDebounceTimeout.current);
        const newTimeout = setTimeout(() => {
            fetchFile();
            fileFetchDebounceTimeout.current = undefined;
        }, FILE_FETCH_DEBOUNCE__MS);
        fileFetchDebounceTimeout.current = newTimeout;
    }, [webSocketPubSubMessage]); // eslint-disable-line react-hooks/exhaustive-deps

    const close = useCallback(() => {
        // Cancel any pending debounced fetch
        clearTimeout(fileFetchDebounceTimeout.current);
        clearTimeout(fileDetailDataFetchDebounceTimeout.current);
        // Unset the data
        dispatch(setFileDetailData({ searchQuery: null, filePreview: null }));
        setFile(undefined);
    }, [dispatch]);

    const toggleFullscreen = useCallback(() => {
        setIsFullscreen((prev) => !prev);
    }, []);

    const hasContent = (file?.content.trim().length ?? 0) > 0;

    const hasHighlights = (Object.keys(file?.highlight ?? {}).length ?? 0) > 0;

    const hasSummary = (file?.summary?.trim().length ?? 0) > 0;

    const hasTranslations =
        (file?.libretranslateLanguageTranslations?.length ?? 0) > 0;

    // dialog not open: don't render dom element
    if (!openDialog) return;

    return (
        <Dialog
            open={openDialog}
            onClose={close}
            maxWidth="xl"
            fullWidth={true}
            fullScreen={isFullscreen}
            slotProps={{
                paper: {
                    sx: {
                        ...(!isFullscreen && { height: "80vh" }),
                    },
                },
            }}
        >
            <DialogTitle
                sx={{
                    display: "flex",
                    flexDirection: "row",
                    alignItems: "center",
                    gap: 2,
                    padding: 2,
                    paddingBottom: 1, // Reduce bottom padding since divider will add spacing
                }}
            >
                {fileDetailData.filePreview && (
                    <FileCardHeader
                        filePreview={fileDetailData.filePreview}
                        additionalActions={[
                            <IconButton
                                key="fullscreen toggle"
                                title={
                                    isFullscreen
                                        ? "Exit Fullscreen"
                                        : "Fullscreen"
                                }
                                aria-label="toggle fullscreen"
                                onClick={toggleFullscreen}
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
                                onClick={close}
                                title={t("common.close")}
                            >
                                <Close />
                            </IconButton>,
                        ]}
                    />
                )}
            </DialogTitle>

            <DialogContent
                style={{
                    display: "flex",
                    flexDirection: "column",
                }}
            >
                <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
                    <Tabs
                        className={styles.tabBar}
                        value={fileDetailData.tab ?? 0}
                        onChange={(_, number) => {
                            dispatch(
                                setFileDetailData({
                                    tab: number,
                                }),
                            );
                        }}
                        aria-label="file detail tabs"
                    >
                        <Tab
                            data-tab-value={FileDetailTab.Rendered}
                            label="Rendered"
                            value={FileDetailTab.Rendered}
                        />
                        <Tab
                            data-tab-value={FileDetailTab.Content}
                            label="Content"
                            value={FileDetailTab.Content}
                            disabled={!hasContent}
                        />
                        <Tab
                            data-tab-value={FileDetailTab.Highlights}
                            label="Highlights"
                            value={FileDetailTab.Highlights}
                            disabled={!hasHighlights}
                        />
                        <Tab
                            data-tab-value={FileDetailTab.RAW}
                            label="Raw"
                            value={FileDetailTab.RAW}
                        />
                        <Tab
                            data-tab-value={FileDetailTab.Summary}
                            label="Summary"
                            value={FileDetailTab.Summary}
                            disabled={!hasSummary}
                        />
                        <Tab
                            data-tab-value={FileDetailTab.Translations}
                            label="Translations"
                            value={FileDetailTab.Translations}
                            disabled={!hasTranslations}
                        />
                    </Tabs>
                </Box>

                <div
                    style={{
                        flex: 1,
                        display: "flex",
                        flexDirection: "column",
                        overflow: "hidden",
                    }}
                >
                    {!file ? (
                        <div>
                            <Skeleton variant="text" />
                            <Skeleton variant="text" />
                            <Skeleton variant="text" />
                            <Skeleton variant="text" />
                            <Skeleton variant="text" />
                            <Skeleton variant="text" />
                        </div>
                    ) : (
                        <>
                            {(() => {
                                switch (fileDetailData.tab) {
                                    default:
                                    case FileDetailTab.Rendered:
                                        return (
                                            <FileRenderer
                                                fileId={file.fileId}
                                                renderedFile={file.renderedFile}
                                                imap={file.imap}
                                            />
                                        );

                                    case FileDetailTab.Content:
                                        return (
                                            <AceEditor
                                                mode={inferAceModeFromMimeType(
                                                    file.type,
                                                )}
                                                ref={editorRef}
                                                value={file.content}
                                                width="100%"
                                                height="100%"
                                                showGutter={true}
                                                readOnly={true}
                                                editorProps={{
                                                    $blockScrolling: true,
                                                }}
                                                wrapEnabled={true}
                                                setOptions={{
                                                    useWorker: false,
                                                }}
                                            />
                                        );

                                    case FileDetailTab.Highlights:
                                        return (
                                            <HighlightList
                                                highlights={
                                                    (file.highlight as {
                                                        // Cast needed here as the
                                                        // generated type does not properly
                                                        // reflect the api type
                                                        [key: string]: string[];
                                                    }) ?? []
                                                }
                                                fullDetails={true}
                                            />
                                        );

                                    case FileDetailTab.RAW:
                                        return (
                                            <AceEditor
                                                mode={"json"}
                                                ref={editorRef}
                                                value={JSON.stringify(
                                                    JSON.parse(file.raw),
                                                    null,
                                                    2,
                                                )}
                                                width="100%"
                                                height="100%"
                                                readOnly={true}
                                                editorProps={{
                                                    $blockScrolling: true,
                                                }}
                                                setOptions={{
                                                    useWorker: false,
                                                }}
                                            />
                                        );

                                    case FileDetailTab.Summary:
                                        return (
                                            <AceEditor
                                                mode={inferAceModeFromMimeType(
                                                    file.type,
                                                )}
                                                ref={editorRef}
                                                value={file.summary ?? ""}
                                                width="100%"
                                                height="100%"
                                                showGutter={true}
                                                readOnly={true}
                                                editorProps={{
                                                    $blockScrolling: true,
                                                }}
                                                wrapEnabled={true}
                                                setOptions={{
                                                    useWorker: false,
                                                }}
                                            />
                                        );

                                    case FileDetailTab.Translations:
                                        return (
                                            <FileTranslations
                                                translations={
                                                    file.libretranslateLanguageTranslations ??
                                                    []
                                                }
                                            />
                                        );
                                }
                            })()}
                        </>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    );
}
