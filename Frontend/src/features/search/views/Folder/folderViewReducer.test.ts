import { describe, expect, it } from "vitest";

import { TreeNodeModel } from "@app/api";

import { folderViewReducer } from "./folderViewReducer";
import {
    FolderViewActionType,
    FolderViewState,
    ROOT_NODE,
} from "./folderViewState";
import { cloneTree } from "./util";

const makeInitialState = (): FolderViewState => ({
    tree: cloneTree(ROOT_NODE),
    expandedNodes: [],
    fileIds: new Set(),
});

describe("folderViewReducer", () => {
    describe("CHILDREN_ADDED — cursor preservation", () => {
        it("preserves an existing cursor when nextPageCursor is undefined", () => {
            const state = makeInitialState();
            // First, establish children and a cursor.
            const withCursor = folderViewReducer(state, {
                type: FolderViewActionType.CHILDREN_ADDED,
                children: [
                    {
                        fullPath: "/folder",
                        fileCount: 1,
                    },
                ],
                parentPath: ROOT_NODE.id,
                nextPageCursor: "//cursor/page2",
            });
            expect(withCursor.tree.nextPageCursor).toBe("//cursor/page2");

            // A count-refresh dispatch (no nextPageCursor field) must not clear it.
            const refreshed = folderViewReducer(withCursor, {
                type: FolderViewActionType.CHILDREN_ADDED,
                children: [
                    {
                        fullPath: "/folder",
                        fileCount: 2,
                    },
                ],
                parentPath: ROOT_NODE.id,
                // nextPageCursor intentionally absent
            });
            expect(refreshed.tree.nextPageCursor).toBe("//cursor/page2");
        });

        it("clears the cursor when nextPageCursor is explicitly null", () => {
            const state = makeInitialState();
            const withCursor = folderViewReducer(state, {
                type: FolderViewActionType.CHILDREN_ADDED,
                children: [],
                parentPath: ROOT_NODE.id,
                nextPageCursor: "//cursor/page2",
            });

            const lastPage = folderViewReducer(withCursor, {
                type: FolderViewActionType.CHILDREN_ADDED,
                children: [],
                parentPath: ROOT_NODE.id,
                nextPageCursor: null,
            });
            expect(lastPage.tree.nextPageCursor).toBeNull();
        });

        it("updates the cursor when a new string cursor is provided", () => {
            const state = makeInitialState();
            const result = folderViewReducer(state, {
                type: FolderViewActionType.CHILDREN_ADDED,
                children: [],
                parentPath: ROOT_NODE.id,
                nextPageCursor: "//cursor/page3",
            });
            expect(result.tree.nextPageCursor).toBe("//cursor/page3");
        });
    });

    describe("CHILDREN_ADDED — node-merge semantics", () => {
        it("preserves loaded subtrees of children when parent is refreshed", () => {
            const state = makeInitialState();
            // Load children of root, one of which has its own children loaded.
            const withChildren = folderViewReducer(state, {
                type: FolderViewActionType.CHILDREN_ADDED,
                children: [{ fullPath: "//s/folder", fileCount: 3 }],
                parentPath: ROOT_NODE.id,
            });
            // Load grandchildren.
            const withGrandchildren = folderViewReducer(withChildren, {
                type: FolderViewActionType.CHILDREN_ADDED,
                children: [{ fullPath: "//s/folder/sub", fileCount: 1 }],
                parentPath: "//s/folder",
            });
            expect(
                withGrandchildren.tree.children?.["//s/folder"]?.children,
            ).toBeDefined();

            // Refresh root children (count update) — grandchildren must survive.
            const refreshed = folderViewReducer(withGrandchildren, {
                type: FolderViewActionType.CHILDREN_ADDED,
                children: [{ fullPath: "//s/folder", fileCount: 5 }],
                parentPath: ROOT_NODE.id,
            });
            expect(
                refreshed.tree.children?.["//s/folder"]?.children?.[
                    "//s/folder/sub"
                ],
            ).toBeDefined();
            // Count was updated.
            expect(refreshed.tree.children?.["//s/folder"]?.fileCount).toBe(5);
        });
    });

    describe("QUERY_CHANGED", () => {
        it("resets the tree to ROOT_NODE and clears expanded nodes", () => {
            const state = makeInitialState();
            const withData = folderViewReducer(state, {
                type: FolderViewActionType.CHILDREN_ADDED,
                children: [{ fullPath: "//s/folder", fileCount: 3 }],
                parentPath: ROOT_NODE.id,
            });
            const withExpanded = folderViewReducer(withData, {
                type: FolderViewActionType.EXPANDED_NODES_CHANGED,
                expandedNodes: [ROOT_NODE.id, "//s/folder"],
            });

            const reset = folderViewReducer(withExpanded, {
                type: FolderViewActionType.QUERY_CHANGED,
            });

            expect(reset.tree.children).toBeUndefined();
            expect(reset.tree.id).toBe(ROOT_NODE.id);
            expect(reset.expandedNodes).toHaveLength(0);
        });

        it("can be applied to an already-reset state without changing it", () => {
            const state = makeInitialState();
            const reset = folderViewReducer(state, {
                type: FolderViewActionType.QUERY_CHANGED,
            });

            expect(reset.tree.children).toBeUndefined();
            expect(reset.expandedNodes).toHaveLength(0);
        });
    });

    describe("EXPANDED_NODES_CHANGED", () => {
        it("replaces the expanded nodes list with the provided list", () => {
            const state = makeInitialState();
            const updated = folderViewReducer(state, {
                type: FolderViewActionType.EXPANDED_NODES_CHANGED,
                expandedNodes: ["//s/a", "//s/b"],
            });

            expect(updated.expandedNodes).toEqual(["//s/a", "//s/b"]);
        });

        it("can collapse all nodes by passing an empty list", () => {
            const state = makeInitialState();
            const expanded = folderViewReducer(state, {
                type: FolderViewActionType.EXPANDED_NODES_CHANGED,
                expandedNodes: ["//s/a", "//s/b"],
            });

            const collapsed = folderViewReducer(expanded, {
                type: FolderViewActionType.EXPANDED_NODES_CHANGED,
                expandedNodes: [],
            });

            expect(collapsed.expandedNodes).toHaveLength(0);
        });
    });

    describe("CHILDREN_LOAD_STARTED", () => {
        it("sets loading=true on the target node", () => {
            const state = makeInitialState();
            const loading = folderViewReducer(state, {
                type: FolderViewActionType.CHILDREN_LOAD_STARTED,
                parentPath: ROOT_NODE.id,
            });

            expect(loading.tree.loading).toBe(true);
        });

        it("does not affect other parts of the tree", () => {
            const state = makeInitialState();
            const withChildren = folderViewReducer(state, {
                type: FolderViewActionType.CHILDREN_ADDED,
                children: [{ fullPath: "//s/folder", fileCount: 1 }],
                parentPath: ROOT_NODE.id,
            });

            const loading = folderViewReducer(withChildren, {
                type: FolderViewActionType.CHILDREN_LOAD_STARTED,
                parentPath: "//s/folder",
            });

            expect(loading.tree.loading).toBeUndefined();
            expect(loading.tree.children?.["//s/folder"]?.loading).toBe(true);
        });
    });

    describe("CHILDREN_LOAD_FINISHED", () => {
        it("clears loading flag after CHILDREN_LOAD_STARTED", () => {
            const state = makeInitialState();
            const loading = folderViewReducer(state, {
                type: FolderViewActionType.CHILDREN_LOAD_STARTED,
                parentPath: ROOT_NODE.id,
            });

            const done = folderViewReducer(loading, {
                type: FolderViewActionType.CHILDREN_LOAD_FINISHED,
                parentPath: ROOT_NODE.id,
            });

            expect(done.tree.loading).toBeUndefined();
        });

        it("clearing loading on a node that never had LOAD_STARTED is a no-op", () => {
            const state = makeInitialState();
            const done = folderViewReducer(state, {
                type: FolderViewActionType.CHILDREN_LOAD_FINISHED,
                parentPath: ROOT_NODE.id,
            });

            expect(done.tree.loading).toBeUndefined();
        });
    });

    describe("SPINE_NODES_MERGED", () => {
        const makeSpineNode = (
            fullPath: string,
            fileId?: string,
        ): TreeNodeModel => ({
            fullPath,
            fileCount: 0,
            unseenCount: 0,
            isUnseen: false,
            flaggedCount: 0,
            isFlagged: false,
            fileId,
        });

        it("injects spine child into parent with no prior children", () => {
            const state = makeInitialState();
            const result = folderViewReducer(state, {
                type: FolderViewActionType.SPINE_NODES_MERGED,
                nodes: [
                    makeSpineNode("//s/folder"),
                    makeSpineNode("//s/folder/file.txt", "file-1"),
                ],
            });
            expect(result.tree.children?.["//s/folder"]).toBeDefined();
        });

        it("preserves existing sibling children alongside injected spine child", () => {
            const state = makeInitialState();
            const withSibling = folderViewReducer(state, {
                type: FolderViewActionType.CHILDREN_ADDED,
                children: [{ fullPath: "//s/other", fileCount: 2 }],
                parentPath: ROOT_NODE.id,
                nextPageCursor: null,
            });
            const result = folderViewReducer(withSibling, {
                type: FolderViewActionType.SPINE_NODES_MERGED,
                nodes: [makeSpineNode("//s/folder")],
            });
            expect(result.tree.children?.["//s/other"]).toBeDefined();
            expect(result.tree.children?.["//s/folder"]).toBeDefined();
        });

        it("preserves grandchildren of existing nodes (does not clobber loaded subtrees)", () => {
            const state = makeInitialState();
            const withFolder = folderViewReducer(state, {
                type: FolderViewActionType.CHILDREN_ADDED,
                children: [{ fullPath: "//s/folder", fileCount: 3 }],
                parentPath: ROOT_NODE.id,
                nextPageCursor: null,
            });
            const withGrandchildren = folderViewReducer(withFolder, {
                type: FolderViewActionType.CHILDREN_ADDED,
                children: [{ fullPath: "//s/folder/sub", fileCount: 1 }],
                parentPath: "//s/folder",
                nextPageCursor: null,
            });
            // Spine inject into the same folder node.
            const result = folderViewReducer(withGrandchildren, {
                type: FolderViewActionType.SPINE_NODES_MERGED,
                nodes: [
                    makeSpineNode("//s/folder"),
                    makeSpineNode("//s/folder/file.txt", "f1"),
                ],
            });
            // Grandchildren must survive.
            expect(
                result.tree.children?.["//s/folder"]?.children?.[
                    "//s/folder/sub"
                ],
            ).toBeDefined();
            // Newly injected spine child is also present.
            expect(
                result.tree.children?.["//s/folder"]?.children?.[
                    "//s/folder/file.txt"
                ],
            ).toBeDefined();
        });
    });

    describe("INITIAL_DATA_LOADED — auto-expand depth", () => {
        it("expands exactly DEFAULT_EXPANDED_NODES_DEPTH-1 levels of children", () => {
            const state = makeInitialState();
            // Build two levels of children below root.
            const withL1 = folderViewReducer(state, {
                type: FolderViewActionType.CHILDREN_ADDED,
                children: [{ fullPath: "//s/a", fileCount: 1 }],
                parentPath: ROOT_NODE.id,
            });
            const withL2 = folderViewReducer(withL1, {
                type: FolderViewActionType.CHILDREN_ADDED,
                children: [{ fullPath: "//s/a/b", fileCount: 1 }],
                parentPath: "//s/a",
            });
            const withL3 = folderViewReducer(withL2, {
                type: FolderViewActionType.CHILDREN_ADDED,
                children: [{ fullPath: "//s/a/b/c", fileCount: 1 }],
                parentPath: "//s/a/b",
            });

            const loaded = folderViewReducer(withL3, {
                type: FolderViewActionType.INITIAL_DATA_LOADED,
            });

            // Root and depth-1 child should be expanded; depth-2 child should not.
            expect(loaded.expandedNodes).toContain(ROOT_NODE.id);
            expect(loaded.expandedNodes).toContain("//s/a");
            expect(loaded.expandedNodes).not.toContain("//s/a/b");
            expect(loaded.expandedNodes).not.toContain("//s/a/b/c");
        });
    });
});
