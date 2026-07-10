import { AttachFile, ExpandMore } from "@mui/icons-material";
import { Box, Chip } from "@mui/material";
import { useState, useRef, useEffect, useCallback, useMemo } from "react";

import { Attachment } from "@app/api";
import { useAppDispatch } from "@app/hooks";
import { openFileTabThunk } from "@app/slices/searchSlice";

import { AttachmentsPopover } from "./AttachmentsPopover";
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

    useEffect(() => {
        const close = () => setAnchorEl(null);
        document.addEventListener("loom:close-menus", close);
        return () => document.removeEventListener("loom:close-menus", close);
    }, []);

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

    const handleOpenDirect = useCallback(
        (fileId: string, background = false) => {
            dispatch(openFileTabThunk({ fileId, background }));
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

    const hasMultiple = attachments.length > 1;

    return (
        <Box ref={parentRef} sx={{ width: "100%", position: "relative" }}>
            {/* Hidden measurement box to calculate total width of all chips */}
            {hasMultiple && (
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

            {hasMultiple && shouldCollapse ? (
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
                                handleOpenDirect(attachment.id, e.ctrlKey)
                            }
                            className={styles.attachmentChip}
                        />
                    ))}
                </Box>
            )}

            {/* Hidden button so the keyboard 'c' shortcut can open the popover
                via clickActionButton("show-attachments"). */}
            {hasMultiple && (
                <button
                    aria-label="show-attachments"
                    style={{ display: "none" }}
                    onClick={() => setAnchorEl(parentRef.current)}
                />
            )}

            {hasMultiple && (
                <AttachmentsPopover
                    attachments={attachments}
                    totalCount={totalCount}
                    anchorEl={anchorEl}
                    onClose={() => setAnchorEl(null)}
                />
            )}
        </Box>
    );
};
