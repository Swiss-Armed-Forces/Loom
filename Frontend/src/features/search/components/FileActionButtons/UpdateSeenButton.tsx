import {
    FiberManualRecord,
    FiberManualRecordOutlined,
    MarkEmailReadOutlined,
    MarkEmailUnreadOutlined,
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
    disableTooltip = false,
}: UpdateSeenButtonProps) => {
    return (
        <UpdateFileButton
            ariaLabel="seen"
            filePreview={filePreview}
            buttonFullWidth={buttonFullWidth}
            disabled={disabled}
            iconOnly={iconOnly}
            colorSecondary={colorSecondary}
            disableTooltip={disableTooltip}
            // The state, not the action: the same amber dot the folder tree
            // marks unseen files with, and the empty ring it leaves behind
            // once the file has been read. A button that drew the action
            // instead said "seen" on an unseen file.
            Icon={fileSeen ? FiberManualRecordOutlined : FiberManualRecord}
            iconColor={fileSeen ? undefined : "primary"}
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
