import { Box, Skeleton, Typography, useMediaQuery } from "@mui/material";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableRow,
} from "@mui/material";
import { tableCellClasses } from "@mui/material/TableCell";
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
    const matchMedia = useMediaQuery("(max-width: 800px)");
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
                            p: 1.5,
                        }}
                    >
                        <Typography
                            variant="subtitle2"
                            sx={{ fontWeight: "bold" }}
                        >
                            {archive.meta.shortName}
                        </Typography>
                        {archive.sha256 != null && (
                            <Typography
                                variant="caption"
                                component="div"
                                sx={{
                                    fontFamily: "monospace",
                                    wordBreak: "break-all",
                                }}
                            >
                                <b>{t("tableView.header.checksumZip")}:</b>{" "}
                                {archive.sha256}
                            </Typography>
                        )}
                        {archive.sha256Encrypted != null && (
                            <Typography
                                variant="caption"
                                component="div"
                                sx={{
                                    fontFamily: "monospace",
                                    wordBreak: "break-all",
                                }}
                            >
                                <b>
                                    {t("tableView.header.checksumEncrypted")}:
                                </b>{" "}
                                {archive.sha256Encrypted}
                            </Typography>
                        )}
                        <Box
                            sx={{
                                display: "flex",
                                gap: 2,
                                mt: 1,
                                flexWrap: "wrap",
                            }}
                        >
                            <Box
                                sx={{
                                    display: "flex",
                                    alignItems: "center",
                                    gap: 0.5,
                                }}
                            >
                                <Typography variant="body2">
                                    <b>{t("tableView.header.state")}:</b>
                                </Typography>
                                <ArchiveStateChip archive={archive} />
                            </Box>
                            <Typography variant="body2">
                                <b>{t("tableView.header.size")}:</b>{" "}
                                {formatFileSize(archive.content.size)}
                            </Typography>
                        </Box>
                        <Typography variant="body2" sx={{ mt: 0.5 }}>
                            <b>{t("tableView.header.uploaded_datetime")}:</b>{" "}
                            {getFormattedDateTime(archive.meta.updatedDatetime)}
                        </Typography>
                        <Typography variant="body2" sx={{ mt: 0.5 }}>
                            <b>{t("tableView.header.query")}:</b>{" "}
                            {archive.meta.query.searchString}
                        </Typography>
                        <Box
                            sx={{
                                mt: 1,
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
        <Table className={styles.resultTable}>
            <TableHead>
                <TableRow>
                    {!matchMedia ? (
                        <>
                            <TableCell style={{ width: "35%" }}>
                                {t("tableView.header.short_name")}
                            </TableCell>
                            <TableCell>{t("tableView.header.state")}</TableCell>
                            <TableCell>{t("tableView.header.size")}</TableCell>
                            <TableCell>
                                {t("tableView.header.uploaded_datetime")}
                            </TableCell>
                            <TableCell>{t("tableView.header.query")}</TableCell>
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
                            {matchMedia && (
                                <Table sx={{ marginTop: "0.5rem" }}>
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>
                                                {t("tableView.header.state")}
                                            </TableCell>
                                            <TableCell>
                                                {t("tableView.header.size")}
                                            </TableCell>
                                            <TableCell>
                                                {t(
                                                    "tableView.header.uploaded_datetime",
                                                )}
                                            </TableCell>
                                            <TableCell>
                                                {t("tableView.header.query")}
                                            </TableCell>
                                            <TableCell>
                                                {t("tableView.header.actions")}
                                            </TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        <TableRow
                                            sx={{
                                                [`& .${tableCellClasses.root}`]:
                                                    {
                                                        borderBottom: "none",
                                                    },
                                            }}
                                        >
                                            <ArchiveInfo archive={archive} />
                                        </TableRow>
                                    </TableBody>
                                </Table>
                            )}
                        </TableCell>
                        {!matchMedia && <ArchiveInfo archive={archive} />}
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
};
