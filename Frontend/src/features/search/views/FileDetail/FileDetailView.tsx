import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

import { useAppSelector } from "@app/hooks";
import {
    selectFileDetailSelection,
    selectFollowDetailTab,
    selectOpenFileTabs,
} from "@app/slices/searchSlice";
import { TOUR_DETAIL_STEP_IDS } from "@app/tours/tourScene";
import { useTour } from "@app/tours/useTour";
import { FileDetailTab } from "@features/common/utils/enums";
import { FileDetailPanel } from "@features/search/components/FileDetailPanel/FileDetailPanel";

import { FileDetailTabStrip } from "./FileDetailTabStrip";
import styles from "./FileDetailView.module.css";
import { useSettledHighlightedFileId } from "./useSettledHighlightedFileId";

/*
 * Hoisted: `sx` is re-serialised by emotion per object, and these are built
 * once per mounted panel per render of this view.
 */
const SHOWN_SX = { display: "flex" } as const;
const HIDDEN_SX = { display: "none" } as const;
const EMPTY_SX = { p: 2, color: "text.secondary" } as const;

const TOUR_DETAIL_TAB: Partial<Record<string, FileDetailTab>> = {
    "detail-translations": FileDetailTab.Translations,
    "detail-highlights": FileDetailTab.Highlights,
    "detail-raw": FileDetailTab.RAW,
};

/**
 * The File Detail sidebar: a strip of tabs over one mounted panel each.
 *
 * Every panel stays mounted while this view is, and all but the one in front
 * are hidden with `display` - which is what preserves an editor's scroll
 * position across a tab switch. The sidebar itself unmounts the lot when it is
 * closed or switched to another pane, so reopening it costs one fetch per tab;
 * the fix for that is a file-content cache beside `files[].preview`, not
 * keeping this subtree alive behind the other panes.
 */
export const FileDetailView = () => {
    const { t } = useTranslation();
    const selection = useAppSelector(selectFileDetailSelection);
    const openFileTabs = useAppSelector(selectOpenFileTabs);
    const followDetailTab = useAppSelector(selectFollowDetailTab);
    const followFileId = useSettledHighlightedFileId();
    const { activeTourStepId, isTourActive, tourDetailFileId } = useTour();

    // The tour's own surface replaces the reader's strip and panels for the
    // duration rather than being drawn beside them: that is what keeps one
    // mounted panel active, and it leaves their tabs untouched afterwards.
    if (
        isTourActive &&
        TOUR_DETAIL_STEP_IDS.has(activeTourStepId ?? "") &&
        tourDetailFileId !== null
    ) {
        return (
            <Box
                className={styles.filePanel}
                data-tour="document-detail"
                sx={SHOWN_SX}
            >
                <FileDetailPanel
                    tabKind="follow"
                    fileId={tourDetailFileId}
                    detailTab={
                        (activeTourStepId
                            ? TOUR_DETAIL_TAB[activeTourStepId]
                            : undefined) ?? FileDetailTab.Rendered
                    }
                    isActive={false}
                    compact
                />
            </Box>
        );
    }

    const followIsOpenTab =
        followFileId !== null &&
        openFileTabs.some((tab) => tab.fileId === followFileId);

    return (
        <div className={styles.view}>
            <FileDetailTabStrip
                selection={selection}
                openFileTabs={openFileTabs}
                followFileId={followFileId}
            />

            {/* The following tab's own panel. Not mounted when the highlighted
            file is already an open tab - that tab's panel stands in for the
            following tab, so that only one panel ever claims the file. */}
            {followFileId !== null && !followIsOpenTab && (
                <Box
                    className={styles.filePanel}
                    sx={selection.kind === "follow" ? SHOWN_SX : HIDDEN_SX}
                >
                    {/* Keyed by the file so that re-targeting replaces the
                    panel rather than changing its `fileId` underneath it: the
                    document body is panel state, and nothing clears it, so a
                    reused panel draws the previous file's content under the
                    new file's header until the fetch lands. */}
                    <FileDetailPanel
                        key={followFileId}
                        tabKind="follow"
                        fileId={followFileId}
                        detailTab={followDetailTab}
                        isActive={selection.kind === "follow"}
                        compact
                    />
                </Box>
            )}

            {openFileTabs.map((tab) => {
                // A panel standing in for the following tab *is* the following
                // tab: it reads and writes that tab's sub-tab, and it runs no
                // auto-actions, because the reader has not opened this file -
                // the highlight has merely landed on it on the way past.
                const standIn =
                    selection.kind === "follow" && tab.fileId === followFileId;
                const shown =
                    standIn ||
                    (selection.kind === "file" &&
                        selection.fileId === tab.fileId);
                return (
                    <Box
                        key={tab.fileId}
                        className={styles.filePanel}
                        sx={shown ? SHOWN_SX : HIDDEN_SX}
                    >
                        <FileDetailPanel
                            tabKind={standIn ? "follow" : "file"}
                            fileId={tab.fileId}
                            detailTab={
                                standIn ? followDetailTab : tab.detailTab
                            }
                            isActive={shown}
                            compact
                        />
                    </Box>
                );
            })}

            {followFileId === null && selection.kind === "follow" && (
                <Typography sx={EMPTY_SX}>
                    {t("toolbar.views.fileDetailEmpty")}
                </Typography>
            )}
        </div>
    );
};
