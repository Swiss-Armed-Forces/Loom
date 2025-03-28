import { TableCell } from "@mui/material";
import { ArchiveHit } from "../../../app/api";
import { formatFileSize, getFormattedDateTime } from "../../search/util";
import { FileSizeLabel } from "../../common/components/FileSizeLabel";
import { ArchiveActions } from "./ArchiveActions";

interface ArchiveInfo {
    archive: ArchiveHit;
}

export function ArchiveInfo({ archive }: ArchiveInfo) {
    return (
        <>
            <TableCell>{archive.content.state}</TableCell>
            <TableCell title={formatFileSize(archive.content.size)}>
                <FileSizeLabel content={archive.content} searchQuery={""} />
            </TableCell>
            <TableCell
                title={getFormattedDateTime(archive.meta.updatedDatetime)}
            >
                <div>{getFormattedDateTime(archive.meta.updatedDatetime)}</div>
            </TableCell>
            <TableCell>{archive.meta.query.searchString}</TableCell>
            <TableCell style={{ whiteSpace: "nowrap" }}>
                <ArchiveActions archive={archive} />
            </TableCell>
        </>
    );
}
