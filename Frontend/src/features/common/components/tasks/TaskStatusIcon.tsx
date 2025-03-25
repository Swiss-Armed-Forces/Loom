import { TaskStatus } from "../../models/Task.ts";
import { RestorePage, Task } from "@mui/icons-material";
import { FC } from "react";
import { TaskFailedIcon } from "./TaskFailedIcon.tsx";

interface TaskStatusIconProps {
    status: TaskStatus;
}

export const TaskStatusIcon: FC<TaskStatusIconProps> = ({ status }) => {
    const getIcon = (status: TaskStatus) => {
        switch (status) {
            case TaskStatus.ERROR:
                return <TaskFailedIcon color={status} />;
            case TaskStatus.WARNING:
                return <RestorePage color={status} />;
            default:
                return <Task color={status} />;
        }
    };

    return getIcon(status);
};
