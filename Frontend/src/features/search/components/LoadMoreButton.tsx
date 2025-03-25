import styles from "./LoadMoreButton.module.css";
import { Button, CircularProgress } from "@mui/material";
import { Refresh } from "@mui/icons-material";
import { useAppDispatch, useAppSelector } from "../../../app/hooks.ts";
import {
    incrementPageNumber,
    selectLastFileSortId,
    selectNumberOfFiles,
    selectPageNumber,
    updatePage,
} from "../searchSlice.ts";
import { selectIsLoading } from "../../common/commonSlice.ts";
import { useTranslation } from "react-i18next";
import { SearchResultCountText } from "./SearchResultCountText.tsx";
import { defaultPageSize } from "../SearchQueryUtils.ts";

export const LoadMoreButton = () => {
    const isLoading = useAppSelector(selectIsLoading);
    const numberOfResults = useAppSelector(selectNumberOfFiles);
    const pageNumber = useAppSelector(selectPageNumber);
    const lastFileSortId = useAppSelector(selectLastFileSortId);

    const { t } = useTranslation();
    const dispatch = useAppDispatch();

    const loadMoreResults = () => {
        dispatch(incrementPageNumber());
        dispatch(updatePage(lastFileSortId));
    };

    return (
        <div className={styles.loadMoreButtonWrapper}>
            <SearchResultCountText />
            {numberOfResults > (pageNumber + 1) * defaultPageSize && (
                <Button
                    startIcon={!isLoading ? <Refresh /> : undefined}
                    className={styles.loadMoreButton}
                    variant="contained"
                    color="secondary"
                    onClick={loadMoreResults}
                >
                    {isLoading ? (
                        <CircularProgress
                            size="1.5rem"
                            className={styles.loadMoreSpinner}
                            color={"primary"}
                        />
                    ) : (
                        <span>{t("generalSearchView.loadMore")}</span>
                    )}
                </Button>
            )}
        </div>
    );
};
