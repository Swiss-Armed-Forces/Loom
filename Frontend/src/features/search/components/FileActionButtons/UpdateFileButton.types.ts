import { SvgIconComponent } from "@mui/icons-material";

import { GetFilePreviewResponse, UpdateFileRequest } from "@app/api";

export enum UpdateFileProperty {
    hidden = "hidden",
    flagged = "flagged",
    seen = "seen",
}

export enum IconColor {
    inherit = "inherit",
    action = "action",
    disabled = "disabled",
    primary = "primary",
    secondary = "secondary",
    error = "error",
    info = "info",
    success = "success",
    warning = "warning",
}

export interface UpdateFileButtonPropsBase {
    filePreview?: GetFilePreviewResponse;
    buttonFullWidth?: boolean;
    disabled?: boolean;
    iconOnly?: boolean;
    colorSecondary?: boolean;
    ariaLabel?: string;
}

export interface UpdateFileButtonProps extends UpdateFileButtonPropsBase {
    Icon: SvgIconComponent;
    iconTitle: string;
    iconColor?: IconColor | undefined;
    actions: UpdateFileDialogActionConfig[];
    property: UpdateFileProperty;
    successMessage: string;
    request: UpdateFileRequest;
}

interface UpdateFileDialogActionBase {
    text: string;
    startIcon: SvgIconComponent;
}

export interface UpdateFileDialogActionConfig extends UpdateFileDialogActionBase {
    request: UpdateFileRequest;
}

export interface UpdateFileDialogAction extends UpdateFileDialogActionBase {
    onClick: () => void;
}
