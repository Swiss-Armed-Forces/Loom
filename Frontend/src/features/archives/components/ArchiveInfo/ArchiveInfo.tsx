import { TableCell } from "@mui/material";

import { ArchiveHit } from "@app/api";
import { FileSizeLabel } from "@features/archives/components";
import {
    formatFileSize,
    getFormattedDateTime,
} from "@features/common/utils/helpers";
import { FileTasksList } from "@features/search/components/ResultCard/FileTasksList";

import { ArchiveActions } from "./ArchiveActions";

interface ArchiveInfo {
    archive: ArchiveHit;
}

export const ArchiveInfo = ({ archive }: ArchiveInfo) => {
    return (
        <>
            <TableCell>
                <div>{archive.content.state}</div>
                <FileTasksList
                    tasksSucceeded={(archive.content.tasksSucceeded ?? []).map(
                        String,
                    )}
                    taskRetried={(archive.content.tasksRetried ?? []).map(
                        String,
                    )}
                    tasksFailed={(archive.content.tasksFailed ?? []).map(
                        String,
                    )}
                />
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
