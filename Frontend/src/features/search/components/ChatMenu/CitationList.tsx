import { ArticleOutlined, ExpandLess, ExpandMore } from "@mui/icons-material";
import { Box, Chip, Collapse, Tooltip, Typography } from "@mui/material";
import { useState } from "react";

import { useAppDispatch } from "@app/hooks";
import { openFileTabThunk } from "@app/slices/searchSlice";

import { ChatCitation, MAX_CHIP_LABEL_LENGTH } from "./ChatWindow.types";

export const CitationList = ({ citations }: { citations: ChatCitation[] }) => {
    const dispatch = useAppDispatch();
    const [open, setOpen] = useState(false);
    if (citations.length === 0) return null;
    return (
        <Box sx={{ mt: 0.75 }}>
            <Box
                sx={{
                    display: "inline-flex",
                    alignItems: "center",
                    cursor: "pointer",
                    color: "text.secondary",
                    userSelect: "none",
                }}
                onClick={() => setOpen((o) => !o)}
            >
                <Typography variant="caption">
                    {citations.length} source{citations.length !== 1 ? "s" : ""}
                </Typography>
                {open ? (
                    <ExpandLess sx={{ fontSize: 14 }} />
                ) : (
                    <ExpandMore sx={{ fontSize: 14 }} />
                )}
            </Box>
            <Collapse in={open}>
                <Box
                    sx={{
                        mt: 0.75,
                        display: "flex",
                        flexWrap: "wrap",
                        gap: 0.5,
                    }}
                >
                    {citations.map((c, i) => {
                        const label =
                            c.text.length > MAX_CHIP_LABEL_LENGTH
                                ? `${c.text.slice(0, MAX_CHIP_LABEL_LENGTH)}…`
                                : c.text;
                        return (
                            <Tooltip key={c.id} title={c.text} placement="top">
                                <Chip
                                    icon={<ArticleOutlined />}
                                    label={`${i + 1}. ${label}`}
                                    size="small"
                                    variant="outlined"
                                    onClick={() =>
                                        dispatch(
                                            openFileTabThunk({
                                                fileId: c.fileId,
                                            }),
                                        )
                                    }
                                    sx={{
                                        fontSize: "0.7rem",
                                        height: 22,
                                        cursor: "pointer",
                                        opacity: 0.8,
                                        "&:hover": { opacity: 1 },
                                        "& .MuiChip-icon": { fontSize: 13 },
                                    }}
                                />
                            </Tooltip>
                        );
                    })}
                </Box>
            </Collapse>
        </Box>
    );
};
