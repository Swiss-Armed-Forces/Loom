import { SimCardAlert } from "@mui/icons-material";

import { TaskStatus } from "../../utils/enums";

interface TaskFailedIconProps {
    color: TaskStatus;
}
export const TaskFailedIcon = ({ color }: TaskFailedIconProps) => {
    return (
        <SimCardAlert
            sx={{
                transform: "rotateY(180deg)",
            }}
            color={color}
        />
    );
};
