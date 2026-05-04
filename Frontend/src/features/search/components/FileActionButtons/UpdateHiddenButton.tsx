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

export const UpdateHiddenButton = ({
    filePreview,
    buttonFullWidth = false,
    disabled = false,
    fileHidden = false,
    iconOnly = false,
    colorSecondary = false,
}: UpdateHiddenButtonProps) => {
    return (
        <UpdateFileButton
            ariaLabel="hidden"
            filePreview={filePreview}
            buttonFullWidth={buttonFullWidth}
            disabled={disabled}
            iconOnly={iconOnly}
            colorSecondary={colorSecondary}
            Icon={
                buttonFullWidth
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
};
