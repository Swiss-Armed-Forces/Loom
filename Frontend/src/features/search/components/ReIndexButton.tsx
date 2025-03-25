import { YoutubeSearchedForOutlined } from "@mui/icons-material";
import { Button, IconButton } from "@mui/material";
import { useTranslation } from "react-i18next";
import {
    scheduleFileIndexing,
    scheduleSingleFileIndexing,
} from "../../../app/api";
import { setBackgroundTaskSpinnerActive } from "../../common/commonSlice";
import { useAppDispatch, useAppSelector } from "../../../app/hooks";
import { toast } from "react-toastify";
import { selectQuery } from "../searchSlice";

interface ReIndexProps {
    file_id?: string;
    disabled?: boolean;
    icon_only?: boolean;
}

export function ReIndexButton({
    file_id,
    disabled = false,
    icon_only = false,
}: ReIndexProps) {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const searchQuery = useAppSelector(selectQuery);

    const startFileReIndex = () => {
        if (!searchQuery) return;
        dispatch(setBackgroundTaskSpinnerActive());
        let result: Promise<void>;
        if (file_id) {
            result = scheduleSingleFileIndexing(file_id);
        } else {
            result = scheduleFileIndexing(searchQuery);
        }

        result
            .then(() => {
                toast.success(
                    "Re-indexing successfully scheduled, this might take a while. Refresh the page to see the results.",
                );
            })
            .catch((err) => {
                toast.error(
                    "Cannot re-index files. Code: " +
                        err.status +
                        ", Text: " +
                        err.text,
                );
            });
    };

    return (
        <>
            {file_id || icon_only ? (
                <IconButton
                    onClick={() => startFileReIndex()}
                    disabled={disabled}
                    title="Re-index"
                    aria-label="re-index"
                >
                    <YoutubeSearchedForOutlined />
                </IconButton>
            ) : (
                <Button
                    onClick={() => startFileReIndex()}
                    disabled={disabled}
                    color="secondary"
                    fullWidth={true}
                    variant={"contained"}
                    startIcon={<YoutubeSearchedForOutlined />}
                >
                    <span className="btn-label">
                        {t("sideMenu.reIndexQueriedFiles")}
                    </span>
                </Button>
            )}
        </>
    );
}
