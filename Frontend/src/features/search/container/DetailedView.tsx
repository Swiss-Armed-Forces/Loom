import { Skeleton } from "@mui/material";
import { useAppSelector } from "../../../app/hooks";
import { selectIsLoading } from "../../common/commonSlice";
import { EmptySearchResults } from "../components/EmptySearchResults";
import { selectFiles, selectHighlightedIndex } from "../searchSlice";
import { SearchResultCountText } from "../components/SearchResultCountText";
import { LoadMoreButton } from "../components/LoadMoreButton";
import { ResultCard } from "./ResultCard";
import styles from "./DetailedView.module.css";
import React from "react";

export const DetailedView: React.FC = React.memo(() => {
    const files = useAppSelector(selectFiles);
    const isLoading = useAppSelector(selectIsLoading);
    const highlightedIndex = useAppSelector(selectHighlightedIndex);

    const fileIds = Object.keys(files);

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
