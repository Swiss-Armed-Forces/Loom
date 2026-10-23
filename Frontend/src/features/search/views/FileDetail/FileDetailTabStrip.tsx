import { Close, PushPin } from "@mui/icons-material";
import { Divider, IconButton, Tab, Tabs, useMediaQuery } from "@mui/material";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    FOLLOW_TAB,
    FileDetailSelection,
    selectionKey,
} from "@app/slices/fileDetailSelection";
import { SearchFileEntry } from "@app/slices/searchFileEntry";
import {
    OpenFileTab,
    closeFileTabThunk,
    focusFileTab,
    focusFollowTab,
    selectFiles,
} from "@app/slices/searchSlice";

import styles from "./FileDetailView.module.css";

const FOLLOW_VALUE = selectionKey(FOLLOW_TAB);

const DIVIDER_SX = { my: 1 } as const;
const TABS_SX = { flex: 1, minWidth: 0 } as const;
const PIN_SX = { fontSize: 14 } as const;
const CLOSE_BUTTON_SX = {
    transition: "opacity 0.2s ease",
    "&:hover": { opacity: 0.7 },
} as const;

/** Everything the strip draws about one file. */
interface TabLabel {
    fileId: string;
    /** Basename, falling back to the id while the preview is still loading. */
    name: string;
    /** Full path for the tooltip, on the same fallback. */
    path: string;
    flagged: boolean;
    unseen: boolean;
}

const tabLabelOf = (
    files: Record<string, SearchFileEntry>,
    fileId: string,
): TabLabel => {
    const preview = files[fileId]?.preview;
    return {
        fileId,
        name: preview?.path.split("/").at(-1) ?? fileId,
        path: preview?.path ?? fileId,
        flagged: preview?.flagged ?? false,
        unseen: preview?.seen === false,
    };
};

/**
 * Compared field by field because the strip subscribes to the file cache, which
 * gets a fresh identity on every preview that lands - dozens a second while the
 * list is scrolling. Each render costs a forced layout per MUI `Tabs`, so the
 * strip has to re-render for a tab's own label and for nothing else.
 */
const labelsEqual = (a: TabLabel[], b: TabLabel[]): boolean =>
    a.length === b.length &&
    a.every((label, i) => {
        const other = b[i];
        return (
            label.fileId === other.fileId &&
            label.name === other.name &&
            label.path === other.path &&
            label.flagged === other.flagged &&
            label.unseen === other.unseen
        );
    });

export interface FileDetailTabStripProps {
    selection: FileDetailSelection;
    openFileTabs: OpenFileTab[];
    /** The file the following tab is showing, or null with nothing
     *  highlighted. */
    followFileId: string | null;
}

/**
 * The File Detail sidebar's tabs.
 *
 * One following tab, which shows whatever is highlighted and re-targets as the
 * reader moves, then the tabs they opened. The following tab is never
 * closable, which is what keeps the strip from ever being empty.
 */
export const FileDetailTabStrip = ({
    selection,
    openFileTabs,
    followFileId,
}: FileDetailTabStripProps) => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();
    const isMobile = useMediaQuery("(max-width:600px)");
    const labels = useAppSelector(
        (state) =>
            openFileTabs.map((tab) =>
                tabLabelOf(selectFiles(state), tab.fileId),
            ),
        labelsEqual,
    );
    const followLabel = useAppSelector((state) =>
        followFileId === null
            ? null
            : tabLabelOf(selectFiles(state), followFileId).path,
    );

    return (
        <div className={styles.tabBar} data-tour="file-detail-tabs">
            <Tabs value={selection.kind === "follow" ? FOLLOW_VALUE : false}>
                <Tab
                    value={FOLLOW_VALUE}
                    onClick={() => dispatch(focusFollowTab())}
                    title={followLabel ?? t("toolbar.views.fileDetailEmpty")}
                    label={
                        <span className={styles.followTabLabel}>
                            <PushPin sx={PIN_SX} />
                            <span className={styles.fileTabName}>
                                {followLabel?.split("/").at(-1) ??
                                    t("toolbar.views.fileDetailFollow")}
                            </span>
                        </span>
                    }
                />
            </Tabs>
            {labels.length > 0 && (
                <>
                    <Divider orientation="vertical" flexItem sx={DIVIDER_SX} />
                    <Tabs
                        // Checked against the tabs actually drawn: a selection
                        // naming a file that is not open yet is a real state on
                        // boot from a #fileId, and MUI logs an error for a
                        // value no child carries.
                        value={
                            selection.kind === "file" &&
                            labels.some(
                                (label) => label.fileId === selection.fileId,
                            )
                                ? selection.fileId
                                : false
                        }
                        onChange={(_, value: string) =>
                            dispatch(focusFileTab(value))
                        }
                        variant="scrollable"
                        scrollButtons="auto"
                        sx={TABS_SX}
                    >
                        {labels.map((label) => (
                            <Tab
                                key={label.fileId}
                                value={label.fileId}
                                onMouseDown={(e) => {
                                    if (e.button === 1) {
                                        e.preventDefault();
                                        dispatch(
                                            closeFileTabThunk(label.fileId),
                                        );
                                    }
                                }}
                                label={
                                    <span className={styles.fileTabLabel}>
                                        <span
                                            className={styles.fileTabName}
                                            title={label.path}
                                            style={{
                                                ...(label.flagged && {
                                                    color: "var(--mui-palette-error-main)",
                                                }),
                                                ...(label.unseen && {
                                                    fontWeight: "bold",
                                                }),
                                            }}
                                        >
                                            {label.name}
                                        </span>
                                        <IconButton
                                            component="span"
                                            size={isMobile ? "medium" : "small"}
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                dispatch(
                                                    closeFileTabThunk(
                                                        label.fileId,
                                                    ),
                                                );
                                            }}
                                            aria-label="close tab"
                                            sx={CLOSE_BUTTON_SX}
                                        >
                                            <Close
                                                sx={{
                                                    fontSize: isMobile
                                                        ? 16
                                                        : 12,
                                                }}
                                            />
                                        </IconButton>
                                    </span>
                                }
                            />
                        ))}
                    </Tabs>
                </>
            )}
        </div>
    );
};
