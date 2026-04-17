import {
    MarkEmailUnreadOutlined,
    MarkEmailReadOutlined,
} from "@mui/icons-material";
import { t } from "i18next";
import { UpdateFileButton } from "./UpdateFileButton";
import {
    UpdateFileButtonPropsBase,
    UpdateFileProperty,
} from "./UpdateFileButton.types";

interface UpdateSeenButtonProps extends UpdateFileButtonPropsBase {
    fileSeen?: boolean;
}

export function UpdateSeenButton({
    filePreview,
    button_full_width = false,
    disabled = false,
    fileSeen = false,
    icon_only = false,
    colorSecondary = false,
}: UpdateSeenButtonProps) {
    return (
        <UpdateFileButton
            ariaLabel="seen"
            filePreview={filePreview}
            button_full_width={button_full_width}
            disabled={disabled}
            icon_only={icon_only}
            colorSecondary={colorSecondary}
            icon={fileSeen ? MarkEmailUnreadOutlined : MarkEmailReadOutlined}
            iconTitle={
                fileSeen
                    ? t("updateFileState.seen.disable")
                    : t("updateFileState.seen.enable")
            }
            actions={[
                {
                    startIcon: MarkEmailReadOutlined,
                    request: { seen: true },
                    text: t("updateFileState.seen.enableFiles"),
                },
                {
                    startIcon: MarkEmailUnreadOutlined,
                    request: { seen: false },
                    text: t("updateFileState.seen.disableFiles"),
                },
            ]}
            property={UpdateFileProperty.seen}
            successMessage={
                fileSeen
                    ? t("updateFileState.seen.scheduledDisableFilesToast")
                    : t("updateFileState.seen.scheduledEnableFilesToast")
            }
            request={{ seen: !fileSeen }}
        />
    );
}
