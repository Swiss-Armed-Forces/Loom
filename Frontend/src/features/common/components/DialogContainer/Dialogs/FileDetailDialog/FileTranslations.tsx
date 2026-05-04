import TranslateIcon from "@mui/icons-material/Translate";
import { Box, ToggleButton, ToggleButtonGroup, Tooltip } from "@mui/material";
import { useState } from "react";
import AceEditorImport from "react-ace";

import { GetFileLanguageTranslations } from "@app/api";
const AceEditor = AceEditorImport.default || AceEditorImport;

interface FileTranslationsProps {
    translations: GetFileLanguageTranslations[];
}

export const FileTranslations = ({ translations }: FileTranslationsProps) => {
    const [translation, setTranslation] = useState<GetFileLanguageTranslations>(
        translations[0],
    );

    const handleChange = (_, language: string | null) => {
        if (language === null) return;
        const newTranslation = translations.find(
            (t) => t.language === language,
        );

        if (newTranslation) setTranslation(newTranslation);
    };

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
            <Box sx={{ p: 2, borderBottom: 1, borderColor: "divider" }}>
                <ToggleButtonGroup
                    value={translation.language}
                    exclusive
                    onChange={handleChange}
                    aria-label="translations"
                    size="small"
                >
                    {translations.map((tr, idx) => (
                        <Tooltip
                            key={`${tr.language}-${idx}`}
                            title={`Confidence: ${tr.confidence}`}
                            placement="top"
                            enterDelay={500}
                        >
                            <ToggleButton
                                value={tr.language}
                                aria-label={tr.language}
                            >
                                <TranslateIcon
                                    sx={{ mr: 1 }}
                                    fontSize="small"
                                />

                                <span>{tr.language}</span>
                            </ToggleButton>
                        </Tooltip>
                    ))}
                </ToggleButtonGroup>
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
