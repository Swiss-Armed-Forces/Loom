import { Button, IconButton, Tooltip } from "@mui/material";
import { type SxProps, type Theme } from "@mui/material/styles";
import { type ReactNode } from "react";

interface FileActionButtonBaseProps {
    icon: ReactNode;
    buttonIcon?: ReactNode;
    label: string;
    onClick: (e: React.MouseEvent<HTMLButtonElement>) => void;
    iconOnly?: boolean;
    disableTooltip?: boolean;
    disabled?: boolean;
    ariaLabel?: string;
    iconButtonSx?: SxProps<Theme>;
    dataTour?: string;
    children?: ReactNode;
}

export const FileActionButtonBase = ({
    icon,
    buttonIcon,
    label,
    onClick,
    iconOnly = false,
    disableTooltip = false,
    disabled = false,
    ariaLabel,
    iconButtonSx,
    dataTour,
    children,
}: FileActionButtonBaseProps) => {
    if (iconOnly) {
        const iconButton = (
            <IconButton
                aria-label={ariaLabel}
                onClick={onClick}
                disabled={disabled}
                sx={iconButtonSx}
                data-tour={dataTour}
            >
                {icon}
            </IconButton>
        );
        return (
            <>
                {disableTooltip ? (
                    iconButton
                ) : (
                    <Tooltip title={label} placement="top">
                        {iconButton}
                    </Tooltip>
                )}
                {children}
            </>
        );
    }

    return (
        <>
            <Button
                onClick={onClick}
                disabled={disabled}
                color="secondary"
                variant="contained"
                startIcon={buttonIcon ?? icon}
                fullWidth
                data-tour={dataTour}
            >
                <span className="btn-label">{label}</span>
            </Button>
            {children}
        </>
    );
};
