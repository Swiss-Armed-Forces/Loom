import { Refresh } from "@mui/icons-material";
import { Button, CircularProgress, Typography } from "@mui/material";
import { useEffect } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    fetchNextPage,
    selectHasMoreResults,
    selectIsPaginating,
    selectLoadedFiles,
    selectPaginationError,
    selectQuery,
    selectVisibleRange,
    updateQuery,
} from "@app/slices/searchSlice";

import { SearchResultCountText } from "../SearchResultCountText/SearchResultCountText";

import styles from "./LoadMoreButton.module.css";
import { shouldFetchNextPage } from "./nextPageTrigger";

/**
 * The end of the result list: the count, and a button when something is wrong.
 *
 * Pages load on their own as this comes into view, so in the ordinary case
 * there is nothing to press. The button is the recovery path — a page request
 * that failed stops the auto-loading, because retrying a failing request once
 * per scroll event would hammer the API and a list that silently stopped
 * growing is indistinguishable from one that has reached the end.
 */
export const LoadMoreButton = () => {
    const isPaginating = useAppSelector(selectIsPaginating);
    const hasMore = useAppSelector(selectHasMoreResults);
    const error = useAppSelector(selectPaginationError);
    const query = useAppSelector(selectQuery);

    const visibleRange = useAppSelector(selectVisibleRange);
    const loadedCount = useAppSelector(selectLoadedFiles);

    const { t } = useTranslation();
    const dispatch = useAppDispatch();

    // Driven by where the user is in the list rather than by this element
    // scrolling into view: the lead is then rows rather than pixels, so it
    // means the same at every spacing, and a list shorter than the viewport
    // still fills itself.
    useEffect(() => {
        if (
            !shouldFetchNextPage({
                visibleRange,
                loadedCount,
                hasMore,
                isPaginating,
                hasError: error !== null,
            })
        ) {
            return;
        }
        dispatch(fetchNextPage());
    }, [visibleRange, loadedCount, hasMore, isPaginating, error, dispatch]);

    // A lapsed point-in-time cannot be resumed: the cursor holds sort values
    // that only mean something inside the snapshot that produced them. The only
    // correct recovery is a fresh snapshot read from the first page.
    const reopen = () =>
        dispatch(updateQuery({ ...query, id: undefined, sortId: null }));

    return (
        <div className={styles.loadMoreButtonWrapper}>
            <SearchResultCountText />
            {isPaginating && (
                <CircularProgress
                    size="1.5rem"
                    className={styles.loadMoreSpinner}
                    color="primary"
                />
            )}
            {error && !isPaginating && (
                <>
                    <Typography
                        variant="caption"
                        color="error"
                        className={styles.loadMoreError}
                    >
                        {error.kind === "expired"
                            ? t("generalSearchView.queryExpiredPaging")
                            : t("generalSearchView.loadMoreFailed", {
                                  error: error.detail,
                              })}
                    </Typography>
                    <Button
                        startIcon={<Refresh />}
                        className={styles.loadMoreButton}
                        variant="contained"
                        color="secondary"
                        onClick={
                            error.kind === "expired"
                                ? reopen
                                : () => dispatch(fetchNextPage())
                        }
                    >
                        {error.kind === "expired"
                            ? t("generalSearchView.reloadResults")
                            : t("generalSearchView.retryLoadMore")}
                    </Button>
                </>
            )}
        </div>
    );
};
