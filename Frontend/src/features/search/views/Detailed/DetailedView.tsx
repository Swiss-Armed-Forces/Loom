import { Skeleton } from "@mui/material";
import React from "react";

import { useAppSelector } from "@app/hooks";
import { selectIsLoading } from "@app/slices/commonSlice";
import { selectFiles, selectHighlightedIndex } from "@app/slices/searchSlice";
import {
    EmptySearchResults,
    LoadMoreButton,
    ResultCard,
    SearchResultCountText,
} from "@features/search/components";

import styles from "./DetailedView.module.css";

export const DetailedView: React.FC = React.memo(() => {
    const files = useAppSelector(selectFiles);
    const isLoading = useAppSelector(selectIsLoading);
    const highlightedIndex = useAppSelector(selectHighlightedIndex);

    // Get fileIds of files with meta
    const fileIds = Object.keys(files).filter(
        (fileId) => files[fileId].meta !== null,
    );

    if (fileIds.length === 0) {
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
            {fileIds.map((fileId, index) => (
                <ResultCard
                    key={fileId}
                    fileId={fileId}
                    index={index}
                    isHighlighted={highlightedIndex === index}
                />
            ))}
            <LoadMoreButton />
        </div>
    );
});

DetailedView.displayName = "DetailedView";
