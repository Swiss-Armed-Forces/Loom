import { useTranslation } from "react-i18next";

import { useAppSelector } from "@app/hooks";
import { selectLoadedFiles, selectTotalFiles } from "@app/slices/searchSlice";

import styles from "./SearchResultCountText.module.css";

/**
 * How much of the result set is in hand, at the end of the list.
 *
 * This is where paging actually happens, so "how much is left below me" is
 * worth saying here even though the tab above reports the whole set. Once
 * everything has loaded there is no progress left to report and it collapses
 * to the count alone, rather than claiming to show 106 of 106.
 */
export const SearchResultCountText = () => {
    const totalFiles = useAppSelector(selectTotalFiles);
    const loadedFiles = useAppSelector(selectLoadedFiles);

    const { t } = useTranslation();
    const complete = loadedFiles >= totalFiles;

    return (
        <div className={styles.resultCount}>
            {complete
                ? t("generalSearchView.resultCountsComplete", {
                      totalCount: totalFiles,
                  })
                : t("generalSearchView.resultCounts", {
                      actualCount: loadedFiles,
                      totalCount: totalFiles,
                  })}
        </div>
    );
};
