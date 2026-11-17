import { YoutubeSearchedForOutlined } from "@mui/icons-material";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import { openDialog } from "@app/slices/commonSlice";
import { selectQuery, selectTotalFiles } from "@app/slices/searchSlice";
import { DialogType } from "@features/common/utils/enums";

import { FileActionButtonBase } from "./FileActionButtonBase";

interface ReIndexProps {
    fileId?: string;
    disabled?: boolean;
    iconOnly?: boolean;
    disableTooltip?: boolean;
}

export const ReIndexButton = ({
    fileId,
    disabled = false,
    iconOnly = false,
    disableTooltip = false,
}: ReIndexProps) => {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const searchQuery = useAppSelector(selectQuery);
    const filesCount = useAppSelector(selectTotalFiles);

    const startReindexProcess = () => {
        if (!searchQuery && !fileId) return;
        if (!fileId && filesCount === 0) return;

        dispatch(
            openDialog({
                id: "",
                type: DialogType.ReIndex,
                props: {
                    fileId: fileId,
                    searchQuery: searchQuery,
                },
            }),
        );
    };

    return (
        <FileActionButtonBase
            icon={<YoutubeSearchedForOutlined />}
            label={t("sideMenu.reIndexQueriedFiles")}
            onClick={() => startReindexProcess()}
            iconOnly={!!fileId || iconOnly}
            disabled={disabled}
            disableTooltip={disableTooltip}
            ariaLabel="re-index"
        />
    );
};
