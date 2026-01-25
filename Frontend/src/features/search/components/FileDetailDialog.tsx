import {
    ArrowForwardTwoTone,
    Close,
    SettingsApplications,
} from "@mui/icons-material";
import {
    Dialog,
    DialogContent,
    DialogTitle,
    IconButton,
    Skeleton,
    Checkbox,
    Menu,
    MenuItem,
    FormControlLabel,
    Tabs,
    Tab,
    Box,
    Tooltip,
} from "@mui/material";
import { useEffect, useState, useRef, MouseEvent } from "react";
import { useTranslation } from "react-i18next";
import { useAppDispatch, useAppSelector } from "../../../app/hooks";
import { GetFileResponse, getFile as getFile } from "../../../app/api";
import AceEditor from "react-ace";
import {
    selectFileDetailData,
    selectQuery,
    setFileDetailData,
} from "../searchSlice";
import styles from "./FileDetailDialog.module.css";
import { HighlightList } from "../container/HighlightList";

import { ShareButton } from "./ShareButton";
import { FileDetailTab } from "../model";
import {
    handleError,
    selectIsLoading,
    startLoadingIndicator,
    stopLoadingIndicator,
} from "../../common/commonSlice";

import "ace-builds/esm-resolver";
import { roundcubeHost } from "../../common/urls";

export function FileDetailDialog() {
    const fileDetailData = useAppSelector(selectFileDetailData);
    const isLoading = useAppSelector(selectIsLoading);
    const dispatch = useAppDispatch();
    const { t } = useTranslation();

    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>();
    const openOptionsMenu = Boolean(anchorEl);
    const searchQuery = useAppSelector(selectQuery);
    const editorRef = useRef<AceEditor>(null);

    const [file, setFile] = useState<GetFileResponse>();

    const [wrapLines, setWraplines] = useState(true);

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

    useEffect(() => {
        if (!searchQuery) return;
        if (!fileDetailData) return;

        async function fetchFile() {
            if (!searchQuery) return;
            if (!fileDetailData) return;

            const response = await getFile(fileDetailData.fileId, searchQuery);
            setFile(response);
        }

        async function load() {
            dispatch(startLoadingIndicator());
            try {
                await Promise.all([fetchFile()]).catch((errorPayload) => {
                    dispatch(handleError(errorPayload));
                });
            } finally {
                dispatch(stopLoadingIndicator());
            }
        }
        load();
    }, [fileDetailData?.fileId, searchQuery]); // eslint-disable-line react-hooks/exhaustive-deps

    const close = () => {
        dispatch(setFileDetailData(null));
    };

    const clickOptionsMenuOpener = (event: MouseEvent<HTMLElement>) => {
        setAnchorEl(event.currentTarget);
    };

    const closeOptionsMenu = () => {
        setAnchorEl(null);
    };

    return (
        <Dialog
            open={!!fileDetailData}
            onClose={close}
            maxWidth="xl"
            fullWidth={true}
            PaperProps={{
                sx: {
                    height: "80vh",
                },
            }}
        >
            {fileDetailData && file && (
                <>
                    <DialogTitle>
                        {file.name}
                        <IconButton
                            aria-label="close"
                            onClick={close}
                            title={t("common.close")}
                            sx={{
                                position: "absolute",
                                right: 8,
                                top: 8,
                                color: (theme) => theme.palette.grey[500],
                            }}
                        >
                            <Close />
                        </IconButton>
                    </DialogTitle>
                    <DialogContent
                        style={{
                            display: "flex",
                            flexDirection: "column",
                        }}
                    >
                        <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
                            <Tabs
                                indicatorColor="secondary"
                                textColor="secondary"
                                className={styles.tabBar}
                                value={
                                    fileDetailData.tab ?? 0 // always use first enum entry as default
                                }
                                onChange={(_, number) => {
                                    dispatch(
                                        setFileDetailData({
                                            ...fileDetailData,
                                            ...{ tab: number },
                                        }),
                                    );
                                }}
                                aria-label="basic tabs example"
                            >
                                <Tab
                                    label="Rendered"
                                    value={FileDetailTab.Rendered}
                                />
                                <Tab
                                    label="Content"
                                    value={FileDetailTab.Content}
                                />
                                <Tab
                                    label="Highlights"
                                    value={FileDetailTab.Highlights}
                                />
                                <Tab label="Raw" value={FileDetailTab.RAW} />
                                <Tab
                                    label="Summary"
                                    value={FileDetailTab.Summary}
                                />
                                {file.libretranslateLanguageTranslations.map(
                                    (t, index) => (
                                        <Tooltip
                                            key={t.language}
                                            title={`Confidence: ${t.confidence}`}
                                            placement="top"
                                            enterDelay={500}
                                        >
                                            <Tab
                                                label={
                                                    <div
                                                        className={
                                                            styles.translationTabButton
                                                        }
                                                    >
                                                        <span>
                                                            {t.language}
                                                        </span>
                                                        <ArrowForwardTwoTone fontSize="small" />
                                                        <span>{"en"}</span>
                                                    </div>
                                                }
                                                value={
                                                    Object.keys(FileDetailTab)
                                                        .length + index
                                                }
                                            ></Tab>
                                        </Tooltip>
                                    ),
                                )}
                                <div className={styles.optionsButton}>
                                    <ShareButton
                                        fileId={fileDetailData.fileId}
                                    />
                                    <IconButton
                                        title="Options"
                                        aria-controls={
                                            openOptionsMenu
                                                ? "options-menu"
                                                : undefined
                                        }
                                        aria-haspopup="true"
                                        aria-expanded={
                                            openOptionsMenu ? "true" : undefined
                                        }
                                        aria-label="options"
                                        onClick={clickOptionsMenuOpener}
                                    >
                                        <SettingsApplications />
                                    </IconButton>
                                </div>
                            </Tabs>
                        </Box>
                        <div style={{ height: "100%" }}>
                            {isLoading ? (
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
                                            case undefined: // default
                                            case FileDetailTab.Rendered:
                                                return file.imap ? (
                                                    <iframe
                                                        src={`${roundcubeHost}?_task=mail&_extwin=1&_action=show&_uid=${file.imap.uid}&_mbox=${encodeURIComponent(file.imap.folder)}`}
                                                        style={{
                                                            width: "100%",
                                                            height: "100%",
                                                            border: "none",
                                                        }}
                                                    ></iframe>
                                                ) : null;

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
                                                        wrapEnabled={wrapLines}
                                                        showGutter={true}
                                                        readOnly={true}
                                                        editorProps={{
                                                            $blockScrolling: true,
                                                        }}
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
                                                                [
                                                                    key: string
                                                                ]: string[];
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
                                                        value={
                                                            // not stupid if it works
                                                            JSON.stringify(
                                                                JSON.parse(
                                                                    file.raw,
                                                                ),
                                                                null,
                                                                2,
                                                            )
                                                        }
                                                        width="100%"
                                                        height="100%"
                                                        wrapEnabled={wrapLines}
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
                                                        value={
                                                            file.summary ?? ""
                                                        }
                                                        width="100%"
                                                        height="100%"
                                                        wrapEnabled={wrapLines}
                                                        showGutter={true}
                                                        readOnly={true}
                                                        editorProps={{
                                                            $blockScrolling: true,
                                                        }}
                                                        setOptions={{
                                                            useWorker: false,
                                                        }}
                                                    />
                                                );

                                            default:
                                                // Handle dynamic tabs (translations)
                                                return (
                                                    <AceEditor
                                                        ref={editorRef}
                                                        value={
                                                            file
                                                                .libretranslateLanguageTranslations[
                                                                fileDetailData.tab -
                                                                    Object.keys(
                                                                        FileDetailTab,
                                                                    ).length
                                                            ]?.text ?? ""
                                                        }
                                                        width="100%"
                                                        height="100%"
                                                        wrapEnabled={wrapLines}
                                                        showGutter={true}
                                                        readOnly={false}
                                                        editorProps={{
                                                            $blockScrolling: true,
                                                        }}
                                                        setOptions={{
                                                            useWorker: false,
                                                        }}
                                                    />
                                                );
                                        }
                                    })()}

                                    <Menu
                                        open={openOptionsMenu}
                                        onClose={closeOptionsMenu}
                                        anchorEl={anchorEl}
                                    >
                                        <MenuItem>
                                            <FormControlLabel
                                                control={
                                                    <Checkbox
                                                        checked={wrapLines}
                                                        onChange={() =>
                                                            setWraplines(
                                                                !wrapLines,
                                                            )
                                                        }
                                                        size="small"
                                                    />
                                                }
                                                label="Wrap Lines"
                                            />
                                        </MenuItem>
                                    </Menu>
                                </>
                            )}
                        </div>
                    </DialogContent>
                </>
            )}
        </Dialog>
    );
}
