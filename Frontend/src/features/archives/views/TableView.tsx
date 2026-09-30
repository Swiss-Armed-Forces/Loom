import { Box, Paper, Skeleton, Typography, useMediaQuery } from "@mui/material";
import {
    Table,
    TableCell,
    TableBody,
    TableHead,
    TableRow,
} from "@mui/material";
import { useTranslation } from "react-i18next";

import { useAppSelector } from "@app/hooks";
import { selectArchives } from "@app/slices/archiveSlice";
import { selectIsLoading } from "@app/slices/commonSlice";
import { ArchiveInfo } from "@features/archives/components";
import { ArchiveActions } from "@features/archives/components/ArchiveInfo/ArchiveActions";
import { ArchiveStateChip } from "@features/archives/components/ArchiveInfo/ArchiveStateChip";
import {
    formatFileSize,
    getFormattedDateTime,
} from "@features/common/utils/helpers";

import styles from "./TableView.module.css";

export const TableView = () => {
    const archives = useAppSelector(selectArchives);
    const isLoading = useAppSelector(selectIsLoading);
    const { t } = useTranslation();
    const isSmallScreen = useMediaQuery("(max-width: 600px)");

    if (isLoading) {
        return (
            <div className={styles.skeletonLoadingContainer}>
                <div className={styles.skeletonLoadingAvatar}>
                    <Skeleton
                        variant="text"
                        style={{ flexGrow: 1 }}
                        height={100}
                    />
                </div>
                <div className={styles.skeletonLoadingAvatar}>
                    <Skeleton
                        variant="text"
                        style={{ flexGrow: 1 }}
                        height={100}
                    />
                </div>
                <div className={styles.skeletonLoadingAvatar}>
                    <Skeleton
                        variant="text"
                        style={{ flexGrow: 1 }}
                        height={100}
                    />
                </div>
            </div>
        );
    }

    if (isSmallScreen) {
        return (
            <Box
                data-tour="archives-list"
                sx={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 1.5,
                    p: 1,
                }}
            >
                {archives.map((archive) => (
                    <Box
                        key={archive.fileId}
                        sx={{
                            border: 1,
                            borderColor: "divider",
                            borderRadius: 1,
                            p: 1,
                            width: "100%",
                            boxSizing: "border-box",
                        }}
                    >
                        <Typography
                            variant="subtitle2"
                            sx={{
                                fontWeight: "bold",
                                mb: 1,
                                wordBreak: "break-word",
                            }}
                        >
                            {archive.meta.shortName}
                        </Typography>

                        {archive.sha256 != null && (
                            <Box
                                sx={{
                                    mb: 0.5,
                                    p: 0.5,
                                    bgcolor: "action.hover",
                                    borderRadius: 0.5,
                                }}
                            >
                                <Typography
                                    variant="caption"
                                    sx={{
                                        fontFamily: "monospace",
                                        wordBreak: "break-all",
                                        fontSize: "0.65rem",
                                        color: "text.secondary",
                                    }}
                                >
                                    <b>{t("tableView.header.checksumZip")}:</b>{" "}
                                    {archive.sha256}
                                </Typography>
                            </Box>
                        )}
                        {archive.sha256Encrypted != null && (
                            <Box
                                sx={{
                                    mb: 0.5,
                                    p: 0.5,
                                    bgcolor: "action.hover",
                                    borderRadius: 0.5,
                                }}
                            >
                                <Typography
                                    variant="caption"
                                    sx={{
                                        fontFamily: "monospace",
                                        wordBreak: "break-all",
                                        fontSize: "0.65rem",
                                        color: "text.secondary",
                                    }}
                                >
                                    <b>
                                        {t(
                                            "tableView.header.checksumEncrypted",
                                        )}
                                        :
                                    </b>{" "}
                                    {archive.sha256Encrypted}
                                </Typography>
                            </Box>
                        )}

                        <Box sx={{ mb: 1 }}>
                            <Typography
                                variant="caption"
                                sx={{
                                    fontWeight: "bold",
                                    display: "block",
                                    mb: 0.25,
                                }}
                            >
                                {t("tableView.header.note")}
                            </Typography>
                            <Paper
                                variant="outlined"
                                sx={{
                                    width: "100%",
                                    p: 0.5,
                                    minHeight: 50,
                                    maxHeight: 50,
                                    overflow: "auto",
                                    bgcolor: "action.hover",
                                    boxSizing: "border-box",
                                }}
                            >
                                <Typography
                                    component="pre"
                                    variant="caption"
                                    sx={{
                                        fontFamily: "monospace",
                                        whiteSpace: "pre-wrap",
                                        wordBreak: "break-word",
                                        m: 0,
                                        fontSize: "0.7rem",
                                        color: archive.meta.note
                                            ? "text.secondary"
                                            : "text.disabled",
                                    }}
                                >
                                    {archive.meta.note || ""}
                                </Typography>
                            </Paper>
                        </Box>

                        <Box
                            sx={{
                                display: "flex",
                                gap: 1,
                                mb: 1,
                                flexWrap: "wrap",
                                alignItems: "center",
                            }}
                        >
                            <Box
                                sx={{
                                    display: "flex",
                                    alignItems: "center",
                                    gap: 0.25,
                                }}
                            >
                                <Typography
                                    variant="caption"
                                    sx={{ fontWeight: "bold" }}
                                >
                                    {t("tableView.header.state")}:
                                </Typography>
                                <ArchiveStateChip archive={archive} />
                            </Box>
                            <Typography variant="caption">
                                <b>{t("tableView.header.size")}:</b>{" "}
                                {formatFileSize(archive.content.size)}
                            </Typography>
                        </Box>

                        <Typography
                            variant="caption"
                            sx={{ mb: 0.5, display: "block" }}
                        >
                            <b>{t("tableView.header.uploaded_datetime")}:</b>{" "}
                            {getFormattedDateTime(archive.meta.updatedDatetime)}
                        </Typography>

                        <Box sx={{ mb: 1 }}>
                            <Typography
                                variant="caption"
                                sx={{
                                    fontWeight: "bold",
                                    display: "block",
                                    mb: 0.25,
                                }}
                            >
                                {t("tableView.header.query")}
                            </Typography>
                            <Paper
                                variant="outlined"
                                sx={{
                                    width: "100%",
                                    p: 0.5,
                                    minHeight: 50,
                                    maxHeight: 50,
                                    overflow: "auto",
                                    bgcolor: "action.hover",
                                    boxSizing: "border-box",
                                }}
                            >
                                <Typography
                                    variant="caption"
                                    sx={{
                                        fontFamily: "monospace",
                                        whiteSpace: "pre-wrap",
                                        wordBreak: "break-word",
                                        m: 0,
                                        fontSize: "0.7rem",
                                        color: "text.secondary",
                                    }}
                                >
                                    {archive.meta.query.searchString}
                                </Typography>
                            </Paper>
                        </Box>

                        <Box
                            sx={{
                                mt: 0.5,
                                display: "flex",
                                justifyContent: "flex-end",
                            }}
                        >
                            <ArchiveActions archive={archive} />
                        </Box>
                    </Box>
                ))}
            </Box>
        );
    }

    return (
        <Table className={styles.resultTable} data-tour="archives-list">
            <TableHead>
                <TableRow>
                    {!isSmallScreen ? (
                        <>
                            <TableCell style={{ width: "30%" }}>
                                {t("tableView.header.short_name")}
                            </TableCell>
                            <TableCell className={styles.noteCell}>
                                {t("tableView.header.note")}
                            </TableCell>
                            <TableCell>{t("tableView.header.state")}</TableCell>
                            <TableCell>{t("tableView.header.size")}</TableCell>
                            <TableCell>
                                {t("tableView.header.uploaded_datetime")}
                            </TableCell>
                            <TableCell className={styles.queryCell}>
                                {t("tableView.header.query")}
                            </TableCell>
                            <TableCell>
                                {t("tableView.header.actions")}
                            </TableCell>
                        </>
                    ) : (
                        <TableCell style={{ width: "35%" }} />
                    )}
                </TableRow>
            </TableHead>
            <TableBody style={{ marginBottom: "100px" }}>
                {archives.map((archive) => (
                    <TableRow key={archive.fileId}>
                        <TableCell className={styles.nameChecksumCell}>
                            <b>{archive.meta.shortName}</b>
                            <br />
                            <small className={styles.checksumText}>
                                {archive.sha256 != null && (
                                    <>
                                        <b>
                                            {t("tableView.header.checksumZip")}:
                                        </b>
                                        <code> {archive.sha256}</code>
                                        <br />
                                    </>
                                )}
                                {archive.sha256Encrypted != null && (
                                    <>
                                        <b>
                                            {t(
                                                "tableView.header.checksumEncrypted",
                                            )}
                                            :
                                        </b>
                                        <code> {archive.sha256Encrypted}</code>
                                    </>
                                )}
                            </small>
                        </TableCell>
                        <ArchiveInfo archive={archive} />
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
};
