import { Box, IconButton, Menu, MenuItem } from "@mui/material";
import React from "react";
import { useTranslation } from "react-i18next";

import { TaskStatusIcon } from "@features/common/components";

import { flowerHost } from "../../../common/urls";
import { TaskStatus } from "../../../common/utils/enums";

import styles from "./FileTasksList.module.css";

interface FileTasksListProps {
    tasksSucceeded: string[];
    taskRetried: string[];
    tasksFailed: string[];
}

export const FileTasksList = ({
    tasksSucceeded: tasksSucceeded,
    taskRetried: tasksRetried,
    tasksFailed: tasksFailed,
}: FileTasksListProps) => {
    const { t } = useTranslation();

    return (
        <Box className={styles.taskListWrapper}>
            {tasksFailed.length > 0 && (
                <FileTaskIcon
                    tasks={tasksFailed}
                    status={TaskStatus.Error}
                    title={t("sideMenu.tasks.failed")}
                />
            )}
            {tasksRetried.length > 0 && (
                <FileTaskIcon
                    tasks={tasksRetried}
                    status={TaskStatus.Warning}
                    title={t("sideMenu.tasks.retried")}
                />
            )}
            {tasksSucceeded.length > 0 && (
                <FileTaskIcon
                    tasks={tasksSucceeded}
                    status={TaskStatus.Success}
                    title={t("sideMenu.tasks.successful")}
                />
            )}
        </Box>
    );
};

export interface FileTaskIconProps {
    tasks: string[];
    title: string;
    status: TaskStatus;
}

export const FileTaskIcon = ({ tasks, status, title }: FileTaskIconProps) => {
    const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>();
    const openDownloadMenu = Boolean(anchorEl);

    const clickDownloadMenuOpener = (event: React.MouseEvent<HTMLElement>) => {
        setAnchorEl(event.currentTarget);
    };

    const closeDownloadMenu = () => {
        setAnchorEl(null);
    };

    return (
        <div>
            <IconButton
                title={title}
                onClick={clickDownloadMenuOpener}
                color={status}
            >
                <TaskStatusIcon status={status}></TaskStatusIcon>
            </IconButton>
            <Menu
                open={openDownloadMenu}
                anchorEl={anchorEl}
                onClose={closeDownloadMenu}
            >
                {tasks.map((task) => {
                    return (
                        <MenuItem
                            component="a"
                            href={`${flowerHost}task/${task}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            key={task}
                            onClick={closeDownloadMenu}
                        >
                            {task}
                        </MenuItem>
                    );
                })}
            </Menu>
        </div>
    );
};
