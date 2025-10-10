import { useRef } from "react";
import { Skeleton } from "@mui/material";
import { useAppSelector } from "../../../app/hooks";
import { selectIsLoading } from "../../common/commonSlice";
import { EmptySearchResults } from "../components/EmptySearchResults";
import { selectFiles } from "../searchSlice";
import { SearchResultCountText } from "../components/SearchResultCountText";
import { LoadMoreButton } from "../components/LoadMoreButton";
import { ResultCard } from "./ResultCard";
import styles from "./DetailedView.module.css";

export function DetailedView() {
    const files = useAppSelector(selectFiles);
    const isLoading = useAppSelector(selectIsLoading);

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
            {Object.values(files).map((file) => {
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
