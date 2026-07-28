import { useTranslation } from "react-i18next";

import { TaskRecord } from "@app/api";
import { DialogProps } from "@app/slices/commonSlice";

import { DialogBase } from "../DialogBase";
import { FileTasks } from "../FileDetailDialog/FileTasks";

interface ArchiveTasksDialogProps extends DialogProps {
    tasks: TaskRecord[];
    archiveName: string;
    archiveState: string;
}

export const ArchiveTasksDialog = ({
    tasks,
    archiveName,
    archiveState,
    ...dialogProps
}: ArchiveTasksDialogProps) => {
    const { t } = useTranslation();
    const visibleTasks =
        archiveState === "created"
            ? tasks.map((task) => ({ ...task, failed: undefined }))
            : tasks;
    return (
        <DialogBase
            {...dialogProps}
            title={t("archives.tasksDialogTitle", { name: archiveName })}
        >
            <FileTasks tasks={visibleTasks} />
        </DialogBase>
    );
};
