import type { Tool } from "@ag-ui/client";

import type { AppDispatch, RootState } from "@app/store";

export interface PassiveFrontendTool {
    definition: Tool;
    interactive: false;
    handler: (args: Record<string, unknown>) => Promise<string>;
}

export type DispatchAccessor = AppDispatch;

export interface InteractiveFrontendTool {
    definition: Tool;
    interactive: true;
}

export type FrontendTool = PassiveFrontendTool | InteractiveFrontendTool;

export type FrontendToolRegistry = Record<string, FrontendTool>;

export type StateAccessor = () => RootState;

export interface FrontendToolSuccess {
    success: true;
    [key: string]: unknown;
}

export interface FrontendToolError {
    success: false;
    error: string;
}

export type FrontendToolResult = FrontendToolSuccess | FrontendToolError;

export const toolSuccess = (data?: Record<string, unknown>): string =>
    JSON.stringify({ success: true, ...data });

export const toolError = (message: string): string =>
    JSON.stringify({ success: false, error: message });
