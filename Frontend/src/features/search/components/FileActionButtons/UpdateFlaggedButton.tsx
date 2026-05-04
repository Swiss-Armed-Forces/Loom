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

export const UpdateFlaggedButton = ({
    filePreview,
    buttonFullWidth = false,
    disabled = false,
    fileFlagged = false,
    iconOnly = false,
    colorSecondary = false,
}: UpdateFlaggedButtonProps) => {
    return (
        <UpdateFileButton
            ariaLabel="flagged"
            filePreview={filePreview}
            buttonFullWidth={buttonFullWidth}
            disabled={disabled}
            iconOnly={iconOnly}
            colorSecondary={colorSecondary}
            Icon={fileFlagged ? Flag : FlagOutlined}
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
};
