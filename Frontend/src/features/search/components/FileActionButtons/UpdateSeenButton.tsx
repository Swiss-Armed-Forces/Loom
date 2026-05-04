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

export const UpdateSeenButton = ({
    filePreview,
    buttonFullWidth = false,
    disabled = false,
    fileSeen = false,
    iconOnly = false,
    colorSecondary = false,
}: UpdateSeenButtonProps) => {
    return (
        <UpdateFileButton
            ariaLabel="seen"
            filePreview={filePreview}
            buttonFullWidth={buttonFullWidth}
            disabled={disabled}
            iconOnly={iconOnly}
            colorSecondary={colorSecondary}
            Icon={fileSeen ? MarkEmailUnreadOutlined : MarkEmailReadOutlined}
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
};
