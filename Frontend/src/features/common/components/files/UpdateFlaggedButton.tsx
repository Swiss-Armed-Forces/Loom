import { Flag, FlagOutlined } from "@mui/icons-material";
import { t } from "i18next";
import { UpdateFileButton } from "./UpdateFileButton";
import {
    IconColor,
    UpdateFileButtonPropsBase,
    UpdateFileProperty,
} from "./UpdateFileButton.types";

interface UpdateFlaggedButtonProps extends UpdateFileButtonPropsBase {
    fileFlagged?: boolean;
}

export function UpdateFlaggedButton({
    filePreview,
    button_full_width = false,
    disabled = false,
    fileFlagged = false,
    icon_only = false,
    colorSecondary = false,
}: UpdateFlaggedButtonProps) {
    return (
        <UpdateFileButton
            ariaLabel="flagged"
            filePreview={filePreview}
            button_full_width={button_full_width}
            disabled={disabled}
            icon_only={icon_only}
            colorSecondary={colorSecondary}
            icon={fileFlagged ? Flag : FlagOutlined}
            iconColor={fileFlagged ? IconColor.error : undefined}
            iconTitle={
                fileFlagged
                    ? t("updateFileState.flagged.disable")
                    : t("updateFileState.flagged.enable")
            }
            actions={[
                {
                    startIcon: Flag,
                    request: { flagged: true },
                    text: t("updateFileState.flagged.enableFiles"),
                },
                {
                    startIcon: FlagOutlined,
                    request: { flagged: false },
                    text: t("updateFileState.flagged.disableFiles"),
                },
            ]}
            property={UpdateFileProperty.flagged}
            successMessage={
                fileFlagged
                    ? t("updateFileState.flagged.scheduledDisableFilesToast")
                    : t("updateFileState.flagged.scheduledEnableFilesToast")
            }
            request={{ flagged: !fileFlagged }}
        />
    );
}
