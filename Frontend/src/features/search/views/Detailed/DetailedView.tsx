import { Divider, Skeleton, Typography } from "@mui/material";
import React, { useMemo } from "react";
import { useTranslation } from "react-i18next";

import { useAppSelector } from "@app/hooks";
import { selectIsLoading } from "@app/slices/commonSlice";
import {
    selectFiles,
    selectHighlightedIndex,
    selectTemporaryFileId,
} from "@app/slices/searchSlice";
import {
    EmptySearchResults,
    LoadMoreButton,
    ResultCard,
} from "@features/search/components";

import styles from "./DetailedView.module.css";

export const DetailedView: React.FC = React.memo(() => {
    const { t } = useTranslation();
    const files = useAppSelector(selectFiles);
    const isLoading = useAppSelector(selectIsLoading);
    const highlightedIndex = useAppSelector(selectHighlightedIndex);
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

    const tempIndex = allFileIds.length;

    return (
        <div className={styles.cardContainer}>
            {temporaryFileId && (
                <>
                    <Divider sx={{ my: 1 }}>
                        <Typography
                            variant="caption"
                            sx={{ color: "text.disabled" }}
                        >
                            {t("detailedView.outsideCurrentResults")}
                        </Typography>
                    </Divider>
                    <ResultCard
                        key={temporaryFileId}
                        fileId={temporaryFileId}
                        index={tempIndex}
                        isHighlighted={highlightedIndex === tempIndex}
                    />
                    <Divider sx={{ mt: 1 }} />
                </>
            )}
            {allFileIds.map((fileId, index) => (
                <ResultCard
                    key={fileId}
                    fileId={fileId}
                    index={index}
                    isHighlighted={highlightedIndex === index}
                    stale={files[fileId].stale ?? false}
                />
            ))}
            <LoadMoreButton />
        </div>
    );
});

DetailedView.displayName = "DetailedView";
