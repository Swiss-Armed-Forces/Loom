import { Chip } from "@mui/material";

import { ArchiveHit } from "@app/api";
import { useAppDispatch } from "@app/hooks";
import { openDialog } from "@app/slices/commonSlice";
import { archiveStateChipColor } from "@features/archives/constants";
import { DialogType } from "@features/common/utils/enums";

interface ArchiveStateChipProps {
    archive: ArchiveHit;
}

export const ArchiveStateChip = ({ archive }: ArchiveStateChipProps) => {
    const dispatch = useAppDispatch();

    const handleOpenTasks = () => {
        dispatch(
            openDialog({
                id: "",
                type: DialogType.ArchiveTasks,
                props: {
                    tasks: archive.content.tasks ?? [],
                    archiveName: archive.meta.shortName,
                    archiveState: archive.content.state,
                },
            }),
        );
    };

    return (
        <Chip
            size="small"
            label={archive.content.state}
            color={archiveStateChipColor[archive.content.state] ?? "default"}
            variant="outlined"
            onClick={handleOpenTasks}
            sx={{
                cursor: "pointer",
                transition: "transform 0.2s ease",
                "&:hover": { transform: "scale(1.1)" },
                "&:active": { transform: "scale(0.95)" },
            }}
        />
    );
};
