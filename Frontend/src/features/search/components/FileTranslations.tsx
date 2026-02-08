import { Box, ToggleButton, ToggleButtonGroup, Tooltip } from "@mui/material";
import TranslateIcon from "@mui/icons-material/Translate";
import AceEditor from "react-ace";
import {
    selectFileDetailDataSelectedTranslationLanguage,
    setFileDetailData,
} from "../searchSlice";
import { useAppDispatch, useAppSelector } from "../../../app/hooks";
import { GetFileLanguageTranslations } from "../../../app/api";

interface FileTranslationsProps {
    translations: GetFileLanguageTranslations[];
}

export function FileTranslations({ translations }: FileTranslationsProps) {
    const selectedTranslationLanguage = useAppSelector(
        selectFileDetailDataSelectedTranslationLanguage,
    );
    const dispatch = useAppDispatch();

    const selected =
        translations.find((t) => t.language === selectedTranslationLanguage) ??
        translations[0];

    const handleChange = (
        _event: React.MouseEvent<HTMLElement>,
        newLanguage: string | null,
    ) => {
        if (newLanguage === null) return;
        dispatch(
            setFileDetailData({
                selectedTranslationLanguage: newLanguage,
            }),
        );
    };

    if (translations.length === 0) {
        return <div>No translations available</div>;
    }

    return (
        <Box
            width="100%"
            height="100%"
            sx={{ display: "flex", flexDirection: "column", height: "100%" }}
        >
            <Box sx={{ p: 2, borderBottom: 1, borderColor: "divider" }}>
                <ToggleButtonGroup
                    value={selected?.language}
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
                    value={selected?.text ?? ""}
                    width="100%"
                    height="100%"
                    showGutter={true}
                    readOnly={false} // matches your previous behavior
                    editorProps={{
                        $blockScrolling: true,
                    }}
                    setOptions={{
                        useWorker: false,
                    }}
                />
            </Box>
        </Box>
    );
}
