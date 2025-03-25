import { Box, IconButton, Menu, MenuItem } from "@mui/material";
import React from "react";
import { useTranslation } from "react-i18next";
import { TaskList, TaskStatus } from "../../models/Task.ts";
import { TaskStatusIcon } from "./TaskStatusIcon.tsx";
import styles from "./Tasks.module.css";
import { flowerHost } from "../../urls.ts";

interface TasksProps {
    tasksSucceeded: string[];
    taskRetried: string[];
    tasksFailed: string[];
}

export function Tasks({
    tasksSucceeded: tasksSucceeded,
    taskRetried: tasksRetried,
    tasksFailed: tasksFailed,
}: TasksProps) {
    const { t } = useTranslation();

    return (
        <Box className={styles.taskListWrapper}>
            {tasksFailed.length > 0 && (
                <TasksList
                    tasks={tasksFailed}
                    status={TaskStatus.ERROR}
                    title={t("sideMenu.tasks.failed")}
                ></TasksList>
            )}
            {tasksRetried.length > 0 && (
                <TasksList
                    tasks={tasksRetried}
                    status={TaskStatus.WARNING}
                    title={t("sideMenu.tasks.retried")}
                ></TasksList>
            )}
            {tasksSucceeded.length > 0 && (
                <TasksList
                    tasks={tasksSucceeded}
                    status={TaskStatus.SUCCESS}
                    title={t("sideMenu.tasks.successful")}
                ></TasksList>
            )}
        </Box>
    );
}
export function TasksList({ tasks, status, title }: TaskList) {
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
}
