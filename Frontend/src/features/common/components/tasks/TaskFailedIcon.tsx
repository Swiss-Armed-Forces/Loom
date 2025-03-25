import { SimCardAlert } from "@mui/icons-material";
import { TaskStatus } from "../../models/Task.ts";
import { FC } from "react";

interface TaskFailedIconProps {
    color: TaskStatus;
}
export const TaskFailedIcon: FC<TaskFailedIconProps> = ({ color }) => {
    return (
        <SimCardAlert
            sx={{
                transform: "rotateY(180deg)",
            }}
            color={color}
        />
    );
};
