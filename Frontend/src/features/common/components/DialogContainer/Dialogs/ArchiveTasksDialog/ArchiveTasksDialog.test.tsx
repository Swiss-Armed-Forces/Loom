import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { TaskRecord } from "@app/api";

const fileTasksMock = vi.hoisted(() => vi.fn());

vi.mock("../DialogBase", () => ({
    DialogBase: ({ children }: { children: React.ReactNode }) => (
        <div>{children}</div>
    ),
}));

vi.mock("../FileDetailDialog/FileTasks", () => ({
    FileTasks: (props: { tasks: TaskRecord[] }) => {
        fileTasksMock(props);
        return null;
    },
}));

vi.mock("react-i18next", () => ({
    useTranslation: () => ({ t: (key: string) => key }),
}));

import { ArchiveTasksDialog } from "./ArchiveTasksDialog";

const baseDialogProps = {
    onClose: vi.fn(),
    id: "",
    isTop: true,
};

const makeTask = (overrides: Partial<TaskRecord> = {}): TaskRecord => ({
    taskName: "worker.create_archive.collect_files",
    failed: [
        {
            taskId: "task-1",
            startedAt: new Date("2026-07-27T10:00:00Z"),
            finishedAt: new Date("2026-07-27T10:00:01Z"),
            duration: 1.0,
            exception: "SomeError: something went wrong",
        },
    ],
    ...overrides,
});

describe("ArchiveTasksDialog", () => {
    it("suppresses failed runs when archiveState is 'created'", () => {
        const task = makeTask();
        render(
            <ArchiveTasksDialog
                {...baseDialogProps}
                tasks={[task]}
                archiveName="my-archive"
                archiveState="created"
            />,
        );
        expect(fileTasksMock).toHaveBeenCalledWith(
            expect.objectContaining({
                tasks: [expect.objectContaining({ failed: undefined })],
            }),
        );
    });

    it("shows failed runs when archiveState is not 'created'", () => {
        const task = makeTask();
        render(
            <ArchiveTasksDialog
                {...baseDialogProps}
                tasks={[task]}
                archiveName="my-archive"
                archiveState="failed"
            />,
        );
        expect(fileTasksMock).toHaveBeenCalledWith(
            expect.objectContaining({
                tasks: [expect.objectContaining({ failed: task.failed })],
            }),
        );
    });
});
