import { Skeleton } from "@mui/material";
import React, { useMemo } from "react";

import { useAppSelector } from "@app/hooks";
import { selectIsLoading } from "@app/slices/commonSlice";
import {
    selectFiles,
    selectHighlightedFileId,
    selectTemporaryFileId,
} from "@app/slices/searchSlice";
import {
    EmptySearchResults,
    LoadMoreButton,
    ResultCard,
} from "@features/search/components";

import styles from "./DetailedView.module.css";

export const DetailedView: React.FC = React.memo(() => {
    const files = useAppSelector(selectFiles);
    const isLoading = useAppSelector(selectIsLoading);
    const highlightedFileId = useAppSelector(selectHighlightedFileId);
    const temporaryFileId = useAppSelector(selectTemporaryFileId);

    const allFileIds = useMemo(
        () =>
            Object.keys(files).filter((fileId) => files[fileId].meta !== null),
        [files],
    );

    if (allFileIds.length === 0 && !temporaryFileId) {
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
            {temporaryFileId && (
                <ResultCard
                    key={temporaryFileId}
                    fileId={temporaryFileId}
                    isHighlighted={temporaryFileId === highlightedFileId}
                    isTemporary
                />
            )}
            {allFileIds.map((fileId) => (
                <ResultCard
                    key={fileId}
                    fileId={fileId}
                    isHighlighted={fileId === highlightedFileId}
                    stale={files[fileId].stale ?? false}
                />
            ))}
            <LoadMoreButton />
        </div>
    );
});

DetailedView.displayName = "DetailedView";
