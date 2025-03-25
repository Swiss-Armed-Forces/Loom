export enum TaskStatus {
    SUCCESS = "success",
    WARNING = "warning",
    ERROR = "error",
}

export interface TaskList {
    tasks: string[];
    title: string;
    status: TaskStatus;
}
