import { Refresh } from "@mui/icons-material";
import { Button, CircularProgress } from "@mui/material";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import { selectIsLoading } from "@app/slices/commonSlice";
import {
    selectLastFileSortId,
    selectTotalFiles,
    selectQuery,
    updateQuery,
    selectLoadedFiles,
} from "@app/slices/searchSlice";

import { SearchResultCountText } from "../SearchResultCountText/SearchResultCountText";

import styles from "./LoadMoreButton.module.css";

export const LoadMoreButton = () => {
    const isLoading = useAppSelector(selectIsLoading);
    const totalFiles = useAppSelector(selectTotalFiles);
    const loadedFiles = useAppSelector(selectLoadedFiles);
    const query = useAppSelector(selectQuery);
    const lastFileSortId = useAppSelector(selectLastFileSortId);

    const { t } = useTranslation();
    const dispatch = useAppDispatch();

    const loadMoreResults = () => {
        dispatch(
            updateQuery({
                id: query?.id, // keep query id
                sortId: lastFileSortId,
            }),
        );
    };

    return (
        <div className={styles.loadMoreButtonWrapper}>
            <SearchResultCountText />
            {totalFiles > loadedFiles && (
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
