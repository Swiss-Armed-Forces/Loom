import { Paper, TableCell, Typography } from "@mui/material";

import { ArchiveHit } from "@app/api";
import { FileSizeLabel } from "@features/archives/components";
import {
    formatFileSize,
    getFormattedDateTime,
} from "@features/common/utils/helpers";

import { ArchiveActions } from "./ArchiveActions";
import styles from "./ArchiveInfo.module.css";
import { ArchiveStateChip } from "./ArchiveStateChip";

interface ArchiveInfo {
    archive: ArchiveHit;
}

export const ArchiveInfo = ({ archive }: ArchiveInfo) => {
    const note = archive.meta.note;

    return (
        <>
            <TableCell className={styles.noteCell}>
                <Paper
                    variant="outlined"
                    sx={{
                        width: "100%",
                        p: 1,
                        minHeight: 80,
                        maxHeight: 80,
                        overflow: "auto",
                        bgcolor: "action.hover",
                        boxSizing: "border-box",
                    }}
                >
                    <Typography
                        component="pre"
                        variant="body2"
                        sx={{
                            fontFamily: "monospace",
                            whiteSpace: "pre-wrap",
                            wordBreak: "break-word",
                            m: 0,
                            color: note ? "text.secondary" : "text.disabled",
                        }}
                    >
                        {note || ""}
                    </Typography>
                </Paper>
            </TableCell>
            <TableCell>
                <ArchiveStateChip archive={archive} />
            </TableCell>
            <TableCell title={formatFileSize(archive.content.size)}>
                <FileSizeLabel content={archive.content} searchQuery={""} />
            </TableCell>
            <TableCell
                title={getFormattedDateTime(archive.meta.updatedDatetime)}
            >
                <div>{getFormattedDateTime(archive.meta.updatedDatetime)}</div>
            </TableCell>
            <TableCell className={styles.queryCell} style={{ padding: 0 }}>
                <Paper
                    variant="outlined"
                    sx={{
                        width: "100%",
                        height: "80px",
                        bgcolor: "action.hover",
                        overflow: "hidden",
                        boxSizing: "border-box",
                    }}
                >
                    <div
                        style={{
                            width: "calc(100% - 16px)",
                            height: "calc(100% - 16px)",
                            overflowX: "auto",
                            overflowY: "hidden",
                            whiteSpace: "nowrap",
                            padding: "8px",
                            boxSizing: "border-box",
                            fontFamily: "monospace",
                            fontSize: "0.875rem",
                            lineHeight: "1.43",
                        }}
                    >
                        <Typography
                            variant="body2"
                            sx={{
                                m: 0,
                                color: "text.secondary",
                                display: "inline",
                                whiteSpace: "nowrap",
                            }}
                        >
                            {archive.meta.query.searchString}
                        </Typography>
                    </div>
                </Paper>
            </TableCell>
            <TableCell style={{ whiteSpace: "nowrap" }}>
                <ArchiveActions archive={archive} />
            </TableCell>
        </>
    );
};
