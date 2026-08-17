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
