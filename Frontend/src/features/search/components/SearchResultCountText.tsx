import styles from "./SearchResultCountText.module.css";
import { selectLoadedFiles, selectTotalFiles } from "../searchSlice.ts";
import { useAppSelector } from "../../../app/hooks.ts";
import { useTranslation } from "react-i18next";

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
