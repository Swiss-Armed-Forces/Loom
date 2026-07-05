import { AttachFile, ExpandMore } from "@mui/icons-material";
import { Chip, Menu, MenuItem, Box } from "@mui/material";
import { useState, useRef, useEffect, useCallback, useMemo } from "react";

import { Attachment } from "@app/api";
import { useAppDispatch } from "@app/hooks";
import { openFileTabThunk } from "@app/slices/searchSlice";

import styles from "./FileAttachments.module.css";

interface FileAttachmentsProps {
    attachments?: Attachment[];
    totalCount?: number; // Total number of attachments (may be > attachments.length)
    maxWidthRatio?: number; // Percentage of container width (0-1), default 0.8 = 80%
}

export const FileAttachments = ({
    attachments,
    totalCount,
    maxWidthRatio = 0.8,
}: FileAttachmentsProps) => {
    const dispatch = useAppDispatch();

    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const [shouldCollapse, setShouldCollapse] = useState(false);

    const containerRef = useRef<HTMLDivElement>(null);
    const parentRef = useRef<HTMLDivElement>(null);

    const showDropdown = Boolean(anchorEl);

    useEffect(() => {
        if (
            containerRef.current &&
            parentRef.current &&
            (attachments?.length ?? 0) > 1
        ) {
            const chipsWidth = containerRef.current.scrollWidth;
            const parentWidth = parentRef.current.offsetWidth;
            const maxAllowedWidth = parentWidth * maxWidthRatio;
            setShouldCollapse(chipsWidth > maxAllowedWidth);
        }
    }, [attachments, maxWidthRatio]);

    const handleOpenDetail = useCallback(
        (fileId: string, background = false) => {
            dispatch(openFileTabThunk({ fileId, background }));
            setAnchorEl(null);
        },
        [dispatch],
    );

    const summaryLabel = useMemo(() => {
        const count = totalCount ?? attachments?.length ?? 0;
        const base = `${count} attachment${count !== 1 ? "s" : ""}`;
        const suffix =
            totalCount && totalCount > (attachments?.length ?? 0)
                ? ` (showing ${attachments?.length ?? 0})`
                : "";
        return `${base}${suffix}`;
    }, [attachments?.length, totalCount]);

    if (!attachments?.length) {
        return null;
    }

    return (
        <Box ref={parentRef} sx={{ width: "100%", position: "relative" }}>
            {/* Hidden measurement box to calculate total width of all chips */}
            {attachments.length > 1 && (
                <Box
                    ref={containerRef}
                    aria-hidden="true"
                    sx={{
                        position: "absolute",
                        visibility: "hidden",
                        pointerEvents: "none",
                        display: "flex",
                        gap: 0.5,
                        whiteSpace: "nowrap",
                        zIndex: -1,
                    }}
                >
                    {attachments.map((a) => (
                        <Chip
                            key={a.id}
                            icon={<AttachFile />}
                            label={a.name}
                            size="small"
                            variant="outlined"
                        />
                    ))}
                </Box>
            )}

            {shouldCollapse ? (
                <>
                    <Chip
                        icon={<AttachFile />}
                        label={summaryLabel}
                        size="small"
                        variant="outlined"
                        onClick={(e) => setAnchorEl(e.currentTarget)}
                        onDelete={(e) => setAnchorEl(e.currentTarget)}
                        deleteIcon={<ExpandMore />}
                        className={styles.attachmentChip}
                    />
                    <Menu
                        anchorEl={anchorEl}
                        open={showDropdown}
                        onClose={() => setAnchorEl(null)}
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
                                onClick={(e) =>
                                    handleOpenDetail(attachment.id, e.ctrlKey)
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
            ) : (
                <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
                    {attachments.map((attachment) => (
                        <Chip
                            key={attachment.id}
                            icon={<AttachFile />}
                            label={attachment.name}
                            size="small"
                            variant="outlined"
                            onClick={(e) =>
                                handleOpenDetail(attachment.id, e.ctrlKey)
                            }
                            className={styles.attachmentChip}
                        />
                    ))}
                </Box>
            )}
        </Box>
    );
};
