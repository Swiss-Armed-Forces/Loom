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
    InputLabel,
    Select,
    FormControl,
    SelectChangeEvent,
} from "@mui/material";
import { useEffect, useState, useRef, MouseEvent } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";
import { useAppDispatch, useAppSelector } from "../../../app/hooks";
import {
    closeFileDetailDialog,
    selectFileDetailData,
} from "../../common/commonSlice";
import {
    GetFileLanguageTranslations,
    GetFileResponse,
    getFullFileContent,
} from "../../../app/api";
import AceEditor from "react-ace";
import { selectQuery } from "../searchSlice";
import styles from "./FileDetailViewDialog.module.css";
import { HighlightList } from "../container/HighlightList";
import { config } from "ace-builds";

import extSearchboxUrl from "ace-builds/src-noconflict/ext-searchbox?url";

import modePlainTextUrl from "ace-builds/src-noconflict/mode-plain_text?url";
import modeCsharpUrl from "ace-builds/src-noconflict/mode-csharp?url";
import modeCssUrl from "ace-builds/src-noconflict/mode-css?url";
import modeGolangUrl from "ace-builds/src-noconflict/mode-golang?url";
import modeHtmlUrl from "ace-builds/src-noconflict/mode-html?url";
import modeJavaScriptUrl from "ace-builds/src-noconflict/mode-javascript?url";
import modeJavaUrl from "ace-builds/src-noconflict/mode-java?url";
import modeJsonUrl from "ace-builds/src-noconflict/mode-json?url";
import modeMarkdownUrl from "ace-builds/src-noconflict/mode-markdown?url";
import modeMysqlUrl from "ace-builds/src-noconflict/mode-mysql?url";
import modePythonUrl from "ace-builds/src-noconflict/mode-python?url";
import modeRubyUrl from "ace-builds/src-noconflict/mode-ruby?url";
import modeSassUrl from "ace-builds/src-noconflict/mode-sass?url";
import modeTypeScriptUrl from "ace-builds/src-noconflict/mode-typescript?url";
import modeXmlUrl from "ace-builds/src-noconflict/mode-xml?url";
import { ShareButton } from "./ShareButton";

config.setModuleUrl("ace/ext/searchbox", extSearchboxUrl);

config.setModuleUrl("ace/mode/plain_text", modePlainTextUrl);
config.setModuleUrl("ace/mode/csharp", modeCsharpUrl);
config.setModuleUrl("ace/mode/css", modeCssUrl);
config.setModuleUrl("ace/mode/golang", modeGolangUrl);
config.setModuleUrl("ace/mode/html", modeHtmlUrl);
config.setModuleUrl("ace/mode/javascript", modeJavaScriptUrl);
config.setModuleUrl("ace/mode/java", modeJavaUrl);
config.setModuleUrl("ace/mode/json", modeJsonUrl);
config.setModuleUrl("ace/mode/markdown", modeMarkdownUrl);
config.setModuleUrl("ace/mode/mysql", modeMysqlUrl);
config.setModuleUrl("ace/mode/python", modePythonUrl);
config.setModuleUrl("ace/mode/ruby", modeRubyUrl);
config.setModuleUrl("ace/mode/sass", modeSassUrl);
config.setModuleUrl("ace/mode/typescript", modeTypeScriptUrl);
config.setModuleUrl("ace/mode/xml", modeXmlUrl);

export function FileDetailViewDialog() {
    const fileDetailData = useAppSelector(selectFileDetailData);
    const dispatch = useAppDispatch();
    const { t } = useTranslation();

    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>();
    const openOptionsMenu = Boolean(anchorEl);
    const searchQuery = useAppSelector(selectQuery);
    const editorRef = useRef<AceEditor>(null);

    const [loading, setLoading] = useState(false);
    const [highlights, setHighlights] = useState<{ [key: string]: any }>({});
    const [content, setContent] = useState<string>("");
    const [libretranslateTranslations, setLibretranslateTranslations] =
        useState<GetFileLanguageTranslations[]>([]);
    const [raw, setRaw] = useState<string>("");
    const [summary, setSummary] = useState<string>("");
    const [file, setFile] = useState<GetFileResponse>();

    const [wrapLines, setWraplines] = useState(true);
    const [tabValue, setTabValue] = useState(0);

    const languages = [
        "plain_text",
        "csharp",
        "css",
        "golang",
        "html",
        "javascript",
        "java",
        "json",
        "markdown",
        "mysql",
        "python",
        "ruby",
        "sass",
        "typescript",
        "xml",
    ];

    interface LanguagesMap {
        [key: string]: string;
    }

    const languagesMap: LanguagesMap = {
        txt: "plain_text",
        cs: "csharp",
        css: "css",
        go: "golang",
        html: "html",
        html5: "html",
        htm: "html",
        js: "javascript",
        java: "java",
        json: "json",
        md: "markdown",
        sql: "mysql",
        py: "python",
        rb: "ruby",
        sass: "sass",
        ts: "typescript",
        xml: "xml",
    };

    const inferModeFromFileName = (fileName: string) => {
        const extension = fileName.split(".").pop()?.toLowerCase() || "";
        return languagesMap[extension] ?? "";
    };

    const [selectedType, setSelectedType] = useState("plain_text"); // default type

    const handleTypeChange = (selectedOption: SelectChangeEvent) => {
        setSelectedType(selectedOption.target.value);
    };

    useEffect(() => {
        if (!searchQuery) return;
        if (!fileDetailData) return;
        setLoading(true);
        Promise.all([
            getFullFileContent(fileDetailData.fileId, searchQuery)
                .then((response) => {
                    setHighlights(response.highlight ?? []);
                    setContent(response.content);
                    setFile(response);
                    // not stupid if it works
                    setRaw(JSON.stringify(JSON.parse(response.raw), null, 2));
                    setSelectedType(inferModeFromFileName(response.name));
                    setSummary(response.summary!);
                    setLibretranslateTranslations(
                        response.libretranslateLanguageTranslations,
                    );
                })
                .catch((err) => {
                    toast.error(
                        "Cannot load full content of file. Reason: " + err,
                    );
                }),
        ]).finally(() => {
            if (fileDetailData.tab !== undefined) {
                setTabValue(fileDetailData.tab);
            }
            setLoading(false);
            location.hash = fileDetailData.fileId;
        });

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [fileDetailData, searchQuery]);

    const close = () => {
        if (tabValue > 2) {
            setTabValue(0);
        }
        location.hash = "";
        dispatch(closeFileDetailDialog());
    };

    const clickOptionsMenuOpener = (event: MouseEvent<HTMLElement>) => {
        setAnchorEl(event.currentTarget);
    };

    const closeOptionsMenu = () => {
        setAnchorEl(null);
    };

    const NUM_STATIC_TABS = 3;

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
                                value={tabValue}
                                onChange={(_, number) => setTabValue(number)}
                                aria-label="basic tabs example"
                            >
                                <Tab label="Content" />
                                <Tab label="Highlights" />
                                <Tab label="Raw" />
                                <Tab label="Summary" />
                                {libretranslateTranslations.map((t) => (
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
                                                    <span>{t.language}</span>
                                                    <ArrowForwardTwoTone fontSize="small" />
                                                    <span>{"en"}</span>
                                                </div>
                                            }
                                        ></Tab>
                                    </Tooltip>
                                ))}
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
                            {loading ? (
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
                                    {tabValue === 0 && (
                                        <AceEditor
                                            mode={selectedType}
                                            ref={editorRef}
                                            value={content}
                                            width="100%"
                                            height="100%"
                                            wrapEnabled={wrapLines}
                                            showGutter={true}
                                            readOnly={true}
                                            editorProps={{
                                                $blockScrolling: true,
                                            }}
                                            setOptions={{ useWorker: false }}
                                        />
                                    )}

                                    {tabValue === 1 && (
                                        <HighlightList
                                            highlights={highlights}
                                            fullDetails={true}
                                        />
                                    )}

                                    {tabValue === 2 && (
                                        <AceEditor
                                            mode="json"
                                            ref={editorRef}
                                            value={raw}
                                            width="100%"
                                            height="100%"
                                            wrapEnabled={wrapLines}
                                            readOnly={true}
                                            editorProps={{
                                                $blockScrolling: true,
                                            }}
                                            setOptions={{ useWorker: false }}
                                        />
                                    )}

                                    {tabValue === 3 && (
                                        <AceEditor
                                            mode={selectedType}
                                            ref={editorRef}
                                            value={summary}
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
                                    )}

                                    {tabValue > NUM_STATIC_TABS && (
                                        <AceEditor
                                            ref={editorRef}
                                            value={
                                                libretranslateTranslations[
                                                    tabValue -
                                                        NUM_STATIC_TABS -
                                                        1
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
                                            setOptions={{ useWorker: false }}
                                        />
                                    )}

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
                                        {tabValue === 0 && (
                                            <MenuItem>
                                                <FormControl fullWidth={true}>
                                                    <InputLabel id="type-select-label">
                                                        Type
                                                    </InputLabel>
                                                    <Select
                                                        labelId="type-select-label"
                                                        id="type-select"
                                                        value={selectedType}
                                                        onChange={
                                                            handleTypeChange
                                                        }
                                                        label="Type"
                                                    >
                                                        {languages.map(
                                                            (
                                                                language,
                                                                index,
                                                            ) => (
                                                                <MenuItem
                                                                    key={index}
                                                                    value={
                                                                        language
                                                                    }
                                                                >
                                                                    {language}
                                                                </MenuItem>
                                                            ),
                                                        )}
                                                    </Select>
                                                </FormControl>
                                            </MenuItem>
                                        )}
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
