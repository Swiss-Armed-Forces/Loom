import { TableCell } from "@mui/material";

import { ArchiveHit } from "@app/api";
import { FileSizeLabel } from "@features/archives/components";
import {
    formatFileSize,
    getFormattedDateTime,
} from "@features/common/utils/helpers";

import { ArchiveActions } from "./ArchiveActions";
import { ArchiveStateChip } from "./ArchiveStateChip";

interface ArchiveInfo {
    archive: ArchiveHit;
}

export const ArchiveInfo = ({ archive }: ArchiveInfo) => {
    return (
        <>
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
            <TableCell>{archive.meta.query.searchString}</TableCell>
            <TableCell style={{ whiteSpace: "nowrap" }}>
                <ArchiveActions archive={archive} />
            </TableCell>
        </>
    );
};
