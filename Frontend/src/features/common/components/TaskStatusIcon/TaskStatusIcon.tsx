import { RestorePage, Task } from "@mui/icons-material";

import { TaskStatus } from "@features/common/utils/enums";

import { TaskFailedIcon } from "./TaskFailedIcon";

interface TaskStatusIconProps {
    status: TaskStatus;
}

export const TaskStatusIcon = ({ status }: TaskStatusIconProps) => {
    const getIcon = (status: TaskStatus) => {
        switch (status) {
            case TaskStatus.Error:
                return <TaskFailedIcon color={status} />;
            case TaskStatus.Warning:
                return <RestorePage color={status} />;
            default:
                return <Task color={status} />;
        }
    };

    return getIcon(status);
};
