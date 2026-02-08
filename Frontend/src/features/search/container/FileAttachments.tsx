import { Chip, Menu, MenuItem, Box } from "@mui/material";
import { AttachFile, ExpandMore } from "@mui/icons-material";
import { useAppDispatch } from "../../../app/hooks";
import styles from "./FileAttachments.module.css";
import { fetchFileDetailData } from "../searchSlice";
import { Attachment } from "../../../app/api";
import { useState, useRef, useEffect } from "react";

interface FileAttachmentsProps {
    attachments?: Attachment[];
    maxWidth?: number; // Maximum width in pixels before collapsing
}
export function FileAttachments({
    attachments,
    maxWidth = 500,
}: FileAttachmentsProps) {
    const dispatch = useAppDispatch();
    const [showDropdown, setShowDropdown] = useState(false);
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const [shouldCollapse, setShouldCollapse] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (containerRef.current && attachments && attachments.length > 1) {
            const width = containerRef.current.scrollWidth;
            setShouldCollapse(width > maxWidth);
        }
    }, [attachments, maxWidth]);

    const handleAttachmentsClick = (attachmentFileId: string) => {
        dispatch(
            fetchFileDetailData({
                fileId: attachmentFileId,
            }),
        );
        handleCloseMenu();
    };

    const handleOpenMenu = (event: React.MouseEvent<HTMLElement>) => {
        setAnchorEl(event.currentTarget);
        setShowDropdown(true);
    };

    const handleCloseMenu = () => {
        setAnchorEl(null);
        setShowDropdown(false);
    };

    if (!attachments || attachments.length === 0) {
        return null;
    }

    // Only render measurement chips when needed
    const measurementChips =
        attachments.length > 1 ? (
            <Box
                ref={containerRef}
                sx={{
                    position: "absolute",
                    visibility: "hidden",
                    display: "flex",
                    gap: "4px",
                    whiteSpace: "nowrap",
                }}
            >
                {attachments.map((attachment) => (
                    <Chip
                        key={attachment.id}
                        icon={<AttachFile />}
                        label={attachment.name}
                        size="small"
                        variant="outlined"
                        className={styles.attachmentChip}
                    />
                ))}
            </Box>
        ) : null;

    // Check if we need to collapse
    if (shouldCollapse) {
        return (
            <>
                <Chip
                    icon={<AttachFile />}
                    label={`${attachments.length} attachments`}
                    size="small"
                    variant="outlined"
                    onClick={handleOpenMenu}
                    onDelete={handleOpenMenu}
                    deleteIcon={<ExpandMore />}
                    className={styles.attachmentChip}
                />
                <Menu
                    anchorEl={anchorEl}
                    open={showDropdown}
                    onClose={handleCloseMenu}
                    anchorOrigin={{
                        vertical: "bottom",
                        horizontal: "left",
                    }}
                    transformOrigin={{
                        vertical: "top",
                        horizontal: "left",
                    }}
                >
                    {attachments.map((attachment) => (
                        <MenuItem
                            key={attachment.id}
                            onClick={() =>
                                handleAttachmentsClick(attachment.id)
                            }
                            sx={{
                                display: "flex",
                                alignItems: "center",
                                gap: 1,
                            }}
                        >
                            <AttachFile fontSize="small" />
                            {attachment.name}
                        </MenuItem>
                    ))}
                </Menu>
            </>
        );
    }

    // Render all chips
    return (
        <>
            {measurementChips}
            <Box sx={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
                {attachments.map((attachment) => (
                    <Chip
                        key={attachment.id}
                        icon={<AttachFile />}
                        label={attachment.name}
                        size="small"
                        variant="outlined"
                        onClick={() => handleAttachmentsClick(attachment.id)}
                        className={styles.attachmentChip}
                    />
                ))}
            </Box>
        </>
    );
}
