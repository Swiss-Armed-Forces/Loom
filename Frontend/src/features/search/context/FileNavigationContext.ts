import { createContext, useContext } from "react";

import { useAppDispatch } from "@app/hooks";
import { openFileTabThunk } from "@app/slices/searchSlice";

export interface FileNavigationValue {
    navigateToFile: (fileId: string, options?: { openInTab?: boolean }) => void;
}

export const FileNavigationContext = createContext<FileNavigationValue | null>(
    null,
);

export const useFileNavigation = () => {
    const context = useContext(FileNavigationContext);
    const dispatch = useAppDispatch();

    // Default value (no provider): open a tab
    if (!context) {
        const fallback: FileNavigationValue = {
            navigateToFile: (
                fileId: string,
                options?: { openInTab?: boolean },
            ) => {
                dispatch(
                    openFileTabThunk({
                        fileId,
                        background: options?.openInTab ?? true,
                    }),
                );
            },
        };
        return fallback;
    }

    return context;
};
