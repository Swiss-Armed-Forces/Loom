import styles from "./SearchResultCountText.module.css";
import { selectNumberOfFiles, selectPageNumber } from "../searchSlice.ts";
import { useAppSelector } from "../../../app/hooks.ts";
import { useTranslation } from "react-i18next";
import { defaultPageSize } from "../SearchQueryUtils.ts";

export const SearchResultCountText = () => {
    const numberOfResults = useAppSelector(selectNumberOfFiles);
    const pageNumber = useAppSelector(selectPageNumber);

    const { t } = useTranslation();

    return (
        <div className={styles.resultCount}>
            {t("generalSearchView.resultCounts", {
                actualCount:
                    (numberOfResults <= (pageNumber + 1) * defaultPageSize &&
                        numberOfResults) ||
                    (pageNumber + 1) * defaultPageSize,
                totalCount: numberOfResults,
            })}
        </div>
    );
};
