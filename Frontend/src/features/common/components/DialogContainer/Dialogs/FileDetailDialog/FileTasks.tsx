import {
    Box,
    Card,
    CardContent,
    CardHeader,
    IconButton,
    Tooltip,
    Typography,
} from "@mui/material";
import { useState } from "react";

import { TaskRecord, TaskRun } from "@app/api";
import { TaskStatusIcon } from "@features/common/components/TaskStatusIcon/TaskStatusIcon";
import { TaskStatus } from "@features/common/utils/enums";

import { ExceptionBlock } from "./ExceptionBlock";
import { ExpandableTextBlock } from "./ExpandableTextBlock";

interface FileTasksProps {
    tasks: TaskRecord[];
}

type RunCategory = "failed" | "retried" | "succeeded";

const toolbarButtonSx = (active: boolean) => ({
    borderRadius: 1,
    p: 0.75,
    filter: active
        ? "none"
        : "grayscale(1) contrast(0) brightness(1.4) opacity(0.5)",
    bgcolor: active ? "action.selected" : "transparent",
    transition: "filter 0.15s ease, transform 0.2s ease",
    "&:hover": { transform: "scale(1.1)" },
});

const formatDateTime = (date: Date) => {
    const base = date.toLocaleString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    });
    const ms = date.getMilliseconds().toString().padStart(3, "0");
    return `${base}.${ms}`;
};

const TaskRunEntry = ({
    run,
    showException,
}: {
    run: TaskRun;
    showException: boolean;
}) => (
    <Box sx={{ mb: 1 }}>
        <Typography variant="caption" color="text.secondary">
            {formatDateTime(run.startedAt)} — {formatDateTime(run.finishedAt)} (
            {run.duration < 1
                ? `${(run.duration * 1000).toFixed(0)}ms`
                : `${run.duration.toFixed(1)}s`}
            )
        </Typography>
        {run.arguments && (
            <ExpandableTextBlock
                text={run.arguments}
                title="Arguments"
                color="text.primary"
                previewDirection="head"
            />
        )}
        {showException && run.exception && (
            <ExceptionBlock text={run.exception} />
        )}
    </Box>
);

const cardStatus = (task: TaskRecord): TaskStatus => {
    if (task.failed?.length) return TaskStatus.Error;
    if (task.retried?.length) return TaskStatus.Warning;
    return TaskStatus.Success;
};

const TaskCard = ({
    task,
    activeCategories,
}: {
    task: TaskRecord;
    activeCategories: RunCategory[];
}) => (
    <Card variant="outlined" sx={{ mb: 1.5 }}>
        <CardHeader
            avatar={<TaskStatusIcon status={cardStatus(task)} />}
            title={
                <Typography variant="subtitle2" sx={{ fontWeight: "bold" }}>
                    {task.taskName}
                </Typography>
            }
            sx={{ pb: 0 }}
        />
        <CardContent sx={{ pt: 1, "&:last-child": { pb: 1 } }}>
            {activeCategories.includes("failed") &&
                (task.failed ?? []).map((run, i) => (
                    <TaskRunEntry key={i} run={run} showException />
                ))}
            {activeCategories.includes("retried") &&
                (task.retried ?? []).map((run, i) => (
                    <TaskRunEntry key={i} run={run} showException />
                ))}
            {activeCategories.includes("succeeded") &&
                (task.succeeded ?? []).map((run, i) => (
                    <TaskRunEntry key={i} run={run} showException={false} />
                ))}
        </CardContent>
    </Card>
);

const hasCategory = (task: TaskRecord, category: RunCategory): boolean => {
    if (category === "failed") return !!task.failed?.length;
    if (category === "retried") return !!task.retried?.length;
    return !!task.succeeded?.length;
};

const sortTasks = (tasks: TaskRecord[]): TaskRecord[] =>
    [...tasks].sort((a, b) => {
        const order = (t: TaskRecord) => {
            if (t.failed?.length) return 0;
            if (t.retried?.length) return 1;
            return 2;
        };
        return order(a) - order(b);
    });

const FILTERS: { category: RunCategory; status: TaskStatus; label: string }[] =
    [
        { category: "failed", status: TaskStatus.Error, label: "Failed" },
        { category: "retried", status: TaskStatus.Warning, label: "Retried" },
        {
            category: "succeeded",
            status: TaskStatus.Success,
            label: "Succeeded",
        },
    ];

export const FileTasks = ({ tasks }: FileTasksProps) => {
    const [activeCategories, setActiveCategories] = useState<RunCategory[]>([
        "failed",
        "retried",
    ]);

    const toggle = (category: RunCategory) => {
        setActiveCategories((prev) => {
            const next = prev.includes(category)
                ? prev.filter((c) => c !== category)
                : [...prev, category];
            return next.length > 0 ? next : prev;
        });
    };

    const visibleTasks = sortTasks(tasks).filter((task) =>
        activeCategories.some((cat) => hasCategory(task, cat)),
    );

    return (
        <Box sx={{ display: "flex", flexDirection: "column", height: "100%" }}>
            <Box
                sx={{
                    px: 1,
                    py: 0.5,
                    borderBottom: 1,
                    borderColor: "divider",
                    display: "flex",
                    alignItems: "center",
                    gap: 0.5,
                }}
            >
                {FILTERS.map(({ category, status, label }) => (
                    <Tooltip key={category} title={label}>
                        <IconButton
                            size="small"
                            onClick={() => toggle(category)}
                            sx={toolbarButtonSx(
                                activeCategories.includes(category),
                            )}
                        >
                            <TaskStatusIcon status={status} />
                        </IconButton>
                    </Tooltip>
                ))}
            </Box>

            <Box sx={{ flex: 1, overflow: "auto", p: 2 }}>
                {visibleTasks.map((task, i) => (
                    <TaskCard
                        key={`${task.taskId}-${i}`}
                        task={task}
                        activeCategories={activeCategories}
                    />
                ))}
                {visibleTasks.length === 0 && (
                    <Typography variant="body2" color="text.secondary">
                        No tasks to show.
                    </Typography>
                )}
            </Box>
        </Box>
    );
};
