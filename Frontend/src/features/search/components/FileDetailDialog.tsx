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
import { useEffect, useState, useRef } from "react";
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

const FILE_FETCH_DEBOUNCE__MS = 2_000;

const inferModeFromMimeType = (mimeType: string | undefined) => {
    const mimeToModeMap: { [key: string]: string } = {
        // Web Technologies
        "text/html": "html",
        "application/xhtml+xml": "html",
        "text/css": "css",
        "text/sass": "sass",
        "text/scss": "scss",
        "text/less": "less",
        "text/stylus": "stylus",

        // JavaScript & TypeScript
        "text/javascript": "javascript",
        "application/javascript": "javascript",
        "application/x-javascript": "javascript",
        "text/typescript": "typescript",
        "application/typescript": "typescript",
        "text/jsx": "jsx",
        "text/tsx": "tsx",
        "application/json": "json",
        "application/ld+json": "json",
        "text/json": "json",

        // Programming Languages
        "text/x-python": "python",
        "application/x-python-code": "python",
        "text/x-java-source": "java",
        "text/x-java": "java",
        "text/x-c": "c_cpp",
        "text/x-c++src": "c_cpp",
        "text/x-c++": "c_cpp",
        "text/x-csharp": "csharp",
        "text/x-php": "php",
        "application/x-php": "php",
        "text/x-ruby": "ruby",
        "application/x-ruby": "ruby",
        "text/x-go": "golang",
        "text/x-rust": "rust",
        "text/x-kotlin": "kotlin",
        "text/x-scala": "scala",
        "text/x-swift": "swift",
        "text/x-objectivec": "objectivec",

        // Functional Languages
        "text/x-haskell": "haskell",
        "text/x-erlang": "erlang",
        "text/x-elixir": "elixir",
        "text/x-clojure": "clojure",
        "text/x-fsharp": "fsharp",
        "text/x-ocaml": "ocaml",
        "text/x-scheme": "scheme",
        "text/x-lisp": "lisp",

        // Shell & Config
        "text/x-shellscript": "sh",
        "application/x-sh": "sh",
        "text/x-bash": "sh",
        "text/x-zsh": "sh",
        "text/x-fish": "sh",
        "text/x-powershell": "powershell",
        "text/x-dockerfile": "dockerfile",
        "text/x-makefile": "makefile",
        "text/x-cmake": "cmake",

        // Markup & Documentation
        "text/xml": "xml",
        "application/xml": "xml",
        "text/markdown": "markdown",
        "text/x-markdown": "markdown",
        "application/x-tex": "latex",
        "text/x-tex": "latex",
        "text/x-rst": "rst",
        "text/x-asciidoc": "asciidoc",

        // Data Formats
        "text/yaml": "yaml",
        "application/x-yaml": "yaml",
        "text/x-yaml": "yaml",
        "text/x-toml": "toml",
        "text/csv": "text",
        "text/tab-separated-values": "text",
        "application/x-ini": "ini",
        "text/x-properties": "properties",

        // Database
        "application/sql": "mysql",
        "text/x-sql": "mysql",
        "text/x-mysql": "mysql",
        "text/x-postgresql": "pgsql",
        "text/x-plsql": "plsql",
        "text/x-cassandra": "cassandra",

        // Web Assembly & Low Level
        "text/x-assembly": "assembly_x86",
        "application/wasm": "wasm",

        // Templating
        "text/x-handlebars": "handlebars",
        "text/x-mustache": "mustache",
        "text/x-twig": "twig",
        "text/x-smarty": "smarty",
        "text/x-velocity": "velocity",
        "text/x-freemarker": "ftl",

        // Game Development
        "text/x-lua": "lua",
        "text/x-glsl": "glsl",
        "text/x-hlsl": "hlsl",

        // Mobile Development
        "text/x-dart": "dart",

        // Scientific Computing
        "text/x-r": "r",
        "text/x-matlab": "matlab",
        "text/x-octave": "matlab",
        "text/x-julia": "julia",

        // Legacy & Specialized
        "text/x-perl": "perl",
        "text/x-tcl": "tcl",
        "text/x-pascal": "pascal",
        "text/x-fortran": "fortran",
        "text/x-cobol": "cobol",
        "text/x-ada": "ada",
        "text/x-vbscript": "vbscript",
        "text/x-vb": "vbscript",
        "text/x-actionscript": "actionscript",

        // Configuration Files
        "text/x-apache-conf": "apache_conf",
        "text/x-nginx-conf": "nginx",
        "text/x-gitignore": "gitignore",
        "text/x-editorconfig": "editorconfig",

        // Default
        "text/plain": "text",
        "application/octet-stream": "text",
    };

    if (!mimeType) return "text";
    return mimeToModeMap[mimeType] ?? "text";
};

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

    // Update ref whenever openDialog changes
    useEffect(() => {
        openDialogRef.current = openDialog;
    }, [openDialog]);

    async function fetchFile() {
        if (!fileDetailData.searchQuery) return;
        if (!fileDetailData.filePreview) return;
        if (!openDialogRef.current) return; // Check current value via ref

        const response = await getFile(fileDetailData.filePreview.fileId, {
            ...fileDetailData.searchQuery,
            id: (await getShortRunningQuery()).queryId,
        });
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

    const close = () => {
        dispatch(setFileDetailData({ searchQuery: null, filePreview: null }));
        setFile(undefined);
    };

    const toggleFullscreen = () => {
        setIsFullscreen(!isFullscreen);
    };

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
                        <Tab label="Rendered" value={FileDetailTab.Rendered} />
                        <Tab label="Raw" value={FileDetailTab.RAW} />
                        <Tab
                            label="Content"
                            value={FileDetailTab.Content}
                            disabled={!hasContent}
                        />
                        <Tab
                            label="Highlights"
                            value={FileDetailTab.Highlights}
                            disabled={!hasHighlights}
                        />
                        <Tab
                            label="Summary"
                            value={FileDetailTab.Summary}
                            disabled={!hasSummary}
                        />
                        <Tab
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
                                                mode={inferModeFromMimeType(
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
                                                mode={inferModeFromMimeType(
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
