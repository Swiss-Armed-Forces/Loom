import { useTranslation } from "react-i18next";

import { useAppSelector } from "@app/hooks";
import { selectLoadedFiles, selectTotalFiles } from "@app/slices/searchSlice";

import styles from "./SearchResultCountText.module.css";

export const SearchResultCountText = () => {
    const totalFiles = useAppSelector(selectTotalFiles);
    const loadedFiles = useAppSelector(selectLoadedFiles);

    const { t } = useTranslation();

    return (
        <div className={styles.resultCount}>
            {t("generalSearchView.resultCounts", {
                actualCount: loadedFiles,
                totalCount: totalFiles,
            })}
        </div>
    );
};
