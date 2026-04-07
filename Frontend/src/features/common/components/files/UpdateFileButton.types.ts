import { SvgIconComponent } from "@mui/icons-material";
import { UpdateFileRequest } from "../../../../app/api";

export enum UpdateFileProperty {
    hidden = "hidden",
    flagged = "flagged",
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
    file_id?: string;
    button_full_width?: boolean;
    disabled?: boolean;
    icon_only?: boolean;
    colorSecondary?: boolean;
}

export interface UpdateFileButtonProps extends UpdateFileButtonPropsBase {
    icon: SvgIconComponent;
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
