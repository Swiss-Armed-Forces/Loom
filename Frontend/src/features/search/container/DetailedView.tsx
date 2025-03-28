import { useEffect, useRef, useState } from "react";
import { Skeleton } from "@mui/material";
import { useAppDispatch, useAppSelector } from "../../../app/hooks";
import {
    selectIsLoading,
    showFileDetailDialog,
} from "../../common/commonSlice";
import { EmptySearchResults } from "../components/EmptySearchResults";
import { selectFiles, selectPageNumber, selectQuery } from "../searchSlice";
import { SearchResultCountText } from "../components/SearchResultCountText";
import { LoadMoreButton } from "../components/LoadMoreButton";
import { ResultCard } from "./ResultCard";
import { defaultPageSize } from "../SearchQueryUtils";
import styles from "./DetailedView.module.css";

export function DetailedView() {
    const dispatch = useAppDispatch();
    const files = useAppSelector(selectFiles);
    const searchQuery = useAppSelector(selectQuery);
    const pageNumber = useAppSelector(selectPageNumber);
    const isLoading = useAppSelector(selectIsLoading);
    const [hasShownInitialDialog, setHasShownInitialDialog] = useState(false);

    useEffect(() => {
        const fileId = window.location.hash.substring(1);
        if (!hasShownInitialDialog && !isLoading && searchQuery) {
            if (fileId && !files[fileId]) {
                dispatch(showFileDetailDialog({ fileId }));
            }
            setHasShownInitialDialog(true);
        }
    }, [
        dispatch,
        files,
        hasShownInitialDialog,
        isLoading,
        pageNumber,
        searchQuery,
    ]);

    const cardRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});

    if (Object.entries(files).length === 0) {
        if (!isLoading) return <EmptySearchResults />;
        return (
            <div className={styles.skeletonLoadingContainer}>
                <div className={styles.skeletonLoadingAvatar}>
                    <Skeleton variant="circular" width={50} height={50} />
                    <Skeleton variant="text" style={{ flexGrow: 1 }} />
                </div>
                <Skeleton variant="text" />
                <Skeleton variant="text" />
                <Skeleton variant="text" />
            </div>
        );
    }

    return (
        <div className={styles.cardContainer}>
            <SearchResultCountText />
            {Object.values(files)
                .slice(0, (pageNumber + 1) * defaultPageSize)
                .map((file) => {
                    return (
                        <ResultCard
                            key={file.meta.fileId}
                            fileId={file.meta.fileId}
                            ref={(el) => {
                                cardRefs.current[file.meta.fileId] = el;
                            }}
                        />
                    );
                })}
            <LoadMoreButton />
        </div>
    );
}
