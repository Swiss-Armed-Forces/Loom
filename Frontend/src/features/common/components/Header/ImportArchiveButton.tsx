import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import { Button } from "@mui/material";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { importArchive } from "@app/api";
import { useAppDispatch } from "@app/hooks";
import { setBackgroundTaskSpinnerActive } from "@app/slices/commonSlice";

export const ImportArchiveButton = () => {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();

    const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        try {
            await importArchive(file);
            toast.success(t("archives.importSuccess"));
            dispatch(setBackgroundTaskSpinnerActive());
        } catch (err) {
            toast.error(t("archives.importError") + err);
        }
        e.target.value = "";
    };

    return (
        <label htmlFor="archive-import-input">
            <input
                id="archive-import-input"
                type="file"
                accept=".zip,.loom"
                hidden
                onChange={handleImport}
            />
            <Button
                component="span"
                variant="outlined"
                startIcon={<CloudUploadIcon />}
                sx={{ color: "white", borderColor: "white" }}
            >
                {t("archives.importButton")}
            </Button>
        </label>
    );
};
