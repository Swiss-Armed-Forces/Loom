import { Skeleton } from "@mui/material";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell, { tableCellClasses } from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import { useTranslation } from "react-i18next";
import { useAppSelector, useMatchMedia } from "../../../app/hooks";
import { selectIsLoading } from "../../common/commonSlice";
import { selectArchives } from "../archiveSlice";
import styles from "./TableView.module.css";
import { ArchiveInfo } from "./ArchiveInfo";

export function TableView() {
    const archives = useAppSelector(selectArchives);
    const isLoading = useAppSelector(selectIsLoading);
    const { t } = useTranslation();
    const matchMedia = useMatchMedia(800);

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
                                {t("tableView.header.checksum")}:
                                <br />
                                <b>{t("tableView.header.checksumZip")}:</b>
                                <code> {archive.sha256}</code>
                                <br />
                                <b>
                                    {t("tableView.header.checksumEncrypted")}:
                                </b>
                                <code> {archive.sha256Encrypted}</code>
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
}
