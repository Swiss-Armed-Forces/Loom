import { AttachFile } from "@mui/icons-material";
import { Menu, MenuItem, Typography } from "@mui/material";

import { Attachment } from "@app/api";
import { useAppDispatch } from "@app/hooks";
import { openFileTabThunk } from "@app/slices/searchSlice";

import { menuJKNavigation } from "../menuKeyboardNav";

interface AttachmentsPopoverProps {
    attachments: Attachment[];
    totalCount?: number;
    anchorEl: HTMLElement | null;
    onClose: () => void;
}

export const AttachmentsPopover = ({
    attachments,
    totalCount,
    anchorEl,
    onClose,
}: AttachmentsPopoverProps) => {
    const dispatch = useAppDispatch();

    const handleOpen = (fileId: string, background = false) => {
        dispatch(openFileTabThunk({ fileId, background }));
        onClose();
    };

    const hiddenCount =
        totalCount !== undefined ? totalCount - attachments.length : 0;

    return (
        <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={onClose}
            onKeyDown={menuJKNavigation}
            anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
            transformOrigin={{ vertical: "top", horizontal: "left" }}
        >
            {attachments.map((attachment) => (
                <MenuItem
                    key={attachment.id}
                    onClick={(e) => handleOpen(attachment.id, e.ctrlKey)}
                    onKeyDown={(e) => {
                        if (e.key === "Enter" && e.ctrlKey) {
                            handleOpen(attachment.id, true);
                        }
                    }}
                    sx={{ gap: 1 }}
                >
                    <AttachFile fontSize="small" />
                    {attachment.name}
                </MenuItem>
            ))}
            {hiddenCount > 0 && (
                <MenuItem disabled>
                    <Typography variant="caption">
                        +{hiddenCount} more not shown
                    </Typography>
                </MenuItem>
            )}
        </Menu>
    );
};
