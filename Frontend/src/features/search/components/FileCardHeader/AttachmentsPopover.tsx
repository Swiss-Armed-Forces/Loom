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

const ATTACHMENT_ITEM_SX = { gap: 1 } as const;

export const AttachmentsPopover = ({
    attachments,
    totalCount,
    anchorEl,
    onClose,
}: AttachmentsPopoverProps) => {
    const dispatch = useAppDispatch();

    // Ctrl keeps the reader where they are; a plain click brings the
    // attachment to the front of the File Detail strip.
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
                    // MUI renders the menu through a portal, but React
                    // synthetic events travel the React tree, not the DOM
                    // tree - so without this the entry's click still reaches
                    // the result card wrapping this popover.
                    onClick={(e) => {
                        e.stopPropagation();
                        handleOpen(attachment.id, e.ctrlKey);
                    }}
                    onKeyDown={(e) => {
                        if (e.key === "Enter" && e.ctrlKey) {
                            e.stopPropagation();
                            handleOpen(attachment.id, true);
                        }
                    }}
                    sx={ATTACHMENT_ITEM_SX}
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
