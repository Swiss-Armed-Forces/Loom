import { Delete, Download, Search, Lock } from "@mui/icons-material";
import { IconButton, Skeleton } from "@mui/material";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../../app/hooks";
import { selectIsLoading } from "../../common/commonSlice";
import { FileSizeLabel } from "../../common/components/FileSizeLabel";
import { setQuery } from "../../search/searchSlice";
import { formatFileSize, getFormattedDateTime } from "../../search/util";
import { removeArchive, selectArchives } from "../archiveSlice";
import styles from "./TableView.module.css";
import { hideArchive } from "../../../app/api";
import { webApiGetArchive, webApiGetArchiveEncrypted } from "../../common/urls";

export function TableView() {
    const archives = useAppSelector(selectArchives);
    const isLoading = useAppSelector(selectIsLoading);
    const dispatch = useAppDispatch();
    const { t } = useTranslation();
    const navigate = useNavigate();

    if (isLoading) {
        return (
            <div className={styles.skeletonLoadingContainer}>
                <div className={styles.skeletonLoadingAvatar}>
                    <Skeleton variant="circular" width={50} height={50} />
                    <Skeleton variant="text" style={{ flexGrow: 1 }} />
                </div>
                <div className={styles.skeletonLoadingAvatar}>
                    <Skeleton variant="circular" width={50} height={50} />
                    <Skeleton variant="text" style={{ flexGrow: 1 }} />
                </div>
                <div className={styles.skeletonLoadingAvatar}>
                    <Skeleton variant="circular" width={50} height={50} />
                    <Skeleton variant="text" style={{ flexGrow: 1 }} />
                </div>
            </div>
        );
    }

    const showArchiveQuery = (archiveId: string) => {
        dispatch(
            setQuery({
                query: `archives:"${archiveId}"`,
            }),
        );
        navigate("/search");
    };

    const handleHideArchive = async (archiveId: string) => {
        await hideArchive(archiveId);
        dispatch(removeArchive(archiveId));
    };

    return (
        <Table className={styles.resultTable}>
            <TableHead>
                <TableRow>
                    <TableCell style={{ width: "35%" }}>
                        {t("tableView.header.short_name")}
                    </TableCell>
                    <TableCell>{t("tableView.header.state")}</TableCell>
                    <TableCell>{t("tableView.header.size")}</TableCell>
                    <TableCell>
                        {t("tableView.header.uploaded_datetime")}
                    </TableCell>
                    <TableCell>{t("tableView.header.query")}</TableCell>
                    <TableCell style={{ width: "220px" }}>
                        {t("tableView.header.actions")}
                    </TableCell>
                </TableRow>
            </TableHead>
            <TableBody style={{ marginBottom: "100px" }}>
                {archives.map((archive) => (
                    <TableRow key={archive.fileId}>
                        <TableCell
                            style={{
                                width: "35%",
                                whiteSpace: "nowrap",
                                wordWrap: "break-word",
                            }}
                        >
                            <b>{archive.meta.shortName}</b>
                            <br />
                            <small>
                                {t("tableView.header.checksum")}:
                                <br />
                                <code>{archive.sha256}</code> (
                                {t("tableView.header.checksumZip")})
                                <br />
                                <code>{archive.sha256Encrypted}</code> (
                                {t("tableView.header.checksumEncrypted")})
                            </small>
                        </TableCell>
                        <TableCell>{archive.content.state}</TableCell>
                        <TableCell title={formatFileSize(archive.content.size)}>
                            <FileSizeLabel
                                content={archive.content}
                                searchQuery={""}
                            />
                        </TableCell>
                        <TableCell
                            title={getFormattedDateTime(
                                archive.meta.updatedDatetime,
                            )}
                        >
                            <div>
                                {getFormattedDateTime(
                                    archive.meta.updatedDatetime,
                                )}
                            </div>
                        </TableCell>
                        <TableCell>{archive.meta.query.searchString}</TableCell>
                        <TableCell
                            style={{ width: "220px", whiteSpace: "nowrap" }}
                        >
                            <IconButton
                                component="a"
                                href={webApiGetArchive(archive.fileId)}
                                target="_blank"
                                rel="noopener noreferrer"
                                title="Download"
                            >
                                <Download color="secondary" />
                            </IconButton>
                            <IconButton
                                component="a"
                                href={webApiGetArchiveEncrypted(archive.fileId)}
                                target="_blank"
                                rel="noopener noreferrer"
                                title="Download Encrypted"
                            >
                                <Lock color="secondary" />
                            </IconButton>
                            <IconButton
                                onClick={() => showArchiveQuery(archive.fileId)}
                            >
                                <Search color="secondary"></Search>
                            </IconButton>
                            {!archive.hidden && (
                                <IconButton
                                    onClick={() =>
                                        handleHideArchive(archive.fileId)
                                    }
                                    title={t("generalSearchView.remove")}
                                >
                                    <Delete color="secondary" />
                                </IconButton>
                            )}
                        </TableCell>
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
}
