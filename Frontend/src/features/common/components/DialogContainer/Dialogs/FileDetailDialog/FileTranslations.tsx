import TranslateIcon from "@mui/icons-material/Translate";
import { Box, ButtonBase, Tooltip } from "@mui/material";
import { useState } from "react";
import AceEditorImport from "react-ace";

import { GetFileLanguageTranslations } from "@app/api";
const AceEditor = (AceEditorImport as any).default ?? AceEditorImport;

interface FileTranslationsProps {
    translations: GetFileLanguageTranslations[];
}

export const FileTranslations = ({ translations }: FileTranslationsProps) => {
    const [translation, setTranslation] = useState<GetFileLanguageTranslations>(
        translations[0],
    );

    if (translations.length === 0) {
        return <div>No translations available</div>;
    }

    return (
        <Box
            sx={{
                width: "100%",
                height: "100%",
                display: "flex",
                flexDirection: "column",
            }}
        >
            <Box
                sx={{
                    px: 1,
                    py: 0.5,
                    borderBottom: 1,
                    borderColor: "divider",
                    display: "flex",
                    alignItems: "center",
                    gap: 0.5,
                }}
            >
                {translations.map((tr, idx) => {
                    const active = tr.language === translation.language;
                    return (
                        <Tooltip
                            key={`${tr.language}-${idx}`}
                            title={`Confidence: ${tr.confidence}`}
                            placement="top"
                            enterDelay={500}
                        >
                            <ButtonBase
                                onClick={() => setTranslation(tr)}
                                sx={{
                                    px: 1,
                                    py: 0.5,
                                    borderRadius: 1,
                                    fontSize: "0.75rem",
                                    fontWeight: active ? 600 : 400,
                                    color: active
                                        ? "primary.main"
                                        : "text.secondary",
                                    bgcolor: active
                                        ? "action.selected"
                                        : "transparent",
                                    display: "flex",
                                    alignItems: "center",
                                    gap: 0.5,
                                    transition:
                                        "transform 0.2s ease, opacity 0.2s ease",
                                    "&:hover": {
                                        transform: "scale(1.05)",
                                        opacity: 0.8,
                                    },
                                }}
                            >
                                <TranslateIcon sx={{ fontSize: "0.9rem" }} />
                                {tr.language}
                            </ButtonBase>
                        </Tooltip>
                    );
                })}
            </Box>
            <Box sx={{ flex: 1, overflow: "hidden" }}>
                <AceEditor
                    mode={"text"}
                    value={translation.text ?? ""}
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
            </Box>
        </Box>
    );
};
