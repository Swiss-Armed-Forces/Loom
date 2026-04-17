import { Visibility, VisibilityOff } from "@mui/icons-material";
import { t } from "i18next";
import { UpdateFileButton } from "./UpdateFileButton";
import {
    IconColor,
    UpdateFileButtonPropsBase,
    UpdateFileProperty,
} from "./UpdateFileButton.types";

interface UpdateHiddenButtonProps extends UpdateFileButtonPropsBase {
    fileHidden?: boolean;
    colorSecondary?: boolean;
}

export function UpdateHiddenButton({
    filePreview,
    button_full_width = false,
    disabled = false,
    fileHidden = false,
    icon_only = false,
    colorSecondary = false,
}: UpdateHiddenButtonProps) {
    return (
        <UpdateFileButton
            ariaLabel="hidden"
            filePreview={filePreview}
            button_full_width={button_full_width}
            disabled={disabled}
            icon_only={icon_only}
            colorSecondary={colorSecondary}
            icon={
                button_full_width
                    ? VisibilityOff
                    : fileHidden
                      ? Visibility
                      : VisibilityOff
            }
            iconColor={colorSecondary ? IconColor.secondary : undefined}
            iconTitle={
                fileHidden
                    ? t("updateFileState.hidden.disable")
                    : t("updateFileState.hidden.enable")
            }
            actions={[
                {
                    startIcon: VisibilityOff,
                    request: { hidden: true },
                    text: t("updateFileState.hidden.enableFiles"),
                },
                {
                    startIcon: Visibility,
                    request: { hidden: false },
                    text: t("updateFileState.hidden.disableFiles"),
                },
            ]}
            property={UpdateFileProperty.hidden}
            successMessage={
                fileHidden
                    ? t("updateFileState.hidden.scheduledDisableFilesToast")
                    : t("updateFileState.hidden.scheduledEnableFilesToast")
            }
            request={{ hidden: !fileHidden }}
        />
    );
}
