import { createContext, RefObject, useContext } from "react";

/**
 * Holds stable refs that each FolderView instance writes its flat ordered list
 * of currently-visible file IDs into. The keyboard navigation hook reads these
 * to move the highlight through the tree with j/k / ArrowUp/ArrowDown.
 *
 * Two separate refs exist — one for each panel side — so both views can be
 * mounted simultaneously without clobbering each other's list.
 */
export interface FolderNavigationRefs {
    leftFolderNavRef: RefObject<string[]>;
    rightFolderNavRef: RefObject<string[]>;
}

export const FolderNavigationContext = createContext<FolderNavigationRefs>({
    leftFolderNavRef: { current: [] },
    rightFolderNavRef: { current: [] },
});

export const useFolderNavigation = () => useContext(FolderNavigationContext);
