import { Chip, Menu, MenuItem, Box } from "@mui/material";
import { AttachFile, ExpandMore } from "@mui/icons-material";
import { useAppDispatch } from "../../../app/hooks";
import styles from "./FileAttachments.module.css";
import { fetchFileDetailData } from "../searchSlice";
import { Attachment } from "../../../app/api";
import { useState, useRef, useEffect } from "react";

interface FileAttachmentsProps {
    attachments?: Attachment[];
    totalCount?: number; // Total number of attachments (may be > attachments.length)
    maxWidthRatio?: number; // Percentage of container width (0-1), default 0.8 = 80%
}

export function FileAttachments({
    attachments,
    totalCount,
    maxWidthRatio = 0.8,
}: FileAttachmentsProps) {
    const dispatch = useAppDispatch();
    const [showDropdown, setShowDropdown] = useState(false);
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const [shouldCollapse, setShouldCollapse] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);
    const parentRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (
            containerRef.current &&
            parentRef.current &&
            attachments &&
            attachments.length > 1
        ) {
            const chipsWidth = containerRef.current.scrollWidth;
            const parentWidth = parentRef.current.offsetWidth;
            const maxAllowedWidth = parentWidth * maxWidthRatio;
            setShouldCollapse(chipsWidth > maxAllowedWidth);
        }
    }, [attachments, maxWidthRatio]);

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
            <Box ref={parentRef} sx={{ width: "100%" }}>
                <Chip
                    icon={<AttachFile />}
                    label={`${totalCount ?? attachments.length} attachments${totalCount && totalCount > attachments.length ? ` (showing ${attachments.length})` : ""}`}
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
            </Box>
        );
    }

    // Render all chips
    return (
        <Box ref={parentRef} sx={{ width: "100%" }}>
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
        </Box>
    );
}
