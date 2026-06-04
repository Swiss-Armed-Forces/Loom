import { ContentCut, LinkOff, Pause } from "@mui/icons-material";
import {
    Badge,
    BadgeProps,
    Box,
    BoxProps,
    CircularProgress,
    CircularProgressProps,
    Tooltip,
    styled,
} from "@mui/material";
import { FC, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useDispatch } from "react-redux";
import { toast } from "react-toastify";

import { useAppSelector } from "@app/hooks";
import {
    fetchQueueStatistics,
    selectQueuesStatistics,
} from "@app/slices/commonSlice";
import {
    fetchAttachmentsSkippedFiles,
    fetchContentTruncatedFiles,
    fetchFailedFiles,
    QUERY_ATTACHMENTS_SKIPPED_FILES,
    QUERY_CONTENT_TRUNCATED_FILES,
    QUERY_FAILED_FILES,
    selectAttachmentsSkippedFilesCount,
    selectContentTruncatedFilesCount,
    selectFailedFilesCount,
    updateQuery,
} from "@app/slices/searchSlice";
import { AppDispatch } from "@app/store";
import { TaskStatusIcon } from "@features/common/components";
import { TaskStatus } from "@features/common/utils/enums";

const CONTENT_TRUNCATED_FILES_POLL_INTERVAL_MS = 180_000;
const ATTACHMENTS_SKIPPED_FILES_POLL_INTERVAL_MS = 180_000;
const FAILED_FILES_POLL_INTERVAL_MS = 180_000;
const QUEUE_STATISTICS_POLL_INTERVAL_MS = 5_000;

export const QUERY_FILES_NOT_PROCESSED =
    "NOT state:processed AND NOT state:failed";

const Indicator = styled(Box)<BoxProps>`
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
`;

const RunningTasksProgress = styled(CircularProgress)<CircularProgressProps>`
    cursor: pointer;
`;

const ErrorCountBadge = styled(Badge)<BadgeProps>`
    cursor: pointer;
`;

export const BackgroundStatusIndicator: FC = () => {
    const contentTruncatedFilesCount = useAppSelector(
        selectContentTruncatedFilesCount,
    );
    const attachmentsSkippedFilesCount = useAppSelector(
        selectAttachmentsSkippedFilesCount,
    );
    const failedBackgroundTaskCount = useAppSelector(selectFailedFilesCount);
    const queueStatistics = useAppSelector(selectQueuesStatistics);
    const { t } = useTranslation();
    const dispatch = useDispatch<AppDispatch>();

    useEffect(() => {
        const load = async () => {
            await Promise.all([
                dispatch(fetchContentTruncatedFiles()),
                dispatch(fetchAttachmentsSkippedFiles()),
                dispatch(fetchFailedFiles()),
                dispatch(fetchQueueStatistics()),
            ]).catch((errorPayload) => {
                toast.error(`Error in load: ${errorPayload}`);
            });
        };
        load();

        const contentTruncatedFilesInterval = setInterval(async () => {
            await dispatch(fetchContentTruncatedFiles()).catch(
                (errorPayload) => {
                    toast.error(
                        `Error in contentTruncatedFilesInterval: ${errorPayload}`,
                    );
                },
            );
        }, CONTENT_TRUNCATED_FILES_POLL_INTERVAL_MS);

        const attachmentsSkippedFilesInterval = setInterval(async () => {
            await dispatch(fetchAttachmentsSkippedFiles()).catch(
                (errorPayload) => {
                    toast.error(
                        `Error in attachmentsSkippedFilesInterval: ${errorPayload}`,
                    );
                },
            );
        }, ATTACHMENTS_SKIPPED_FILES_POLL_INTERVAL_MS);

        const failedFilesInterval = setInterval(async () => {
            await dispatch(fetchFailedFiles()).catch((errorPayload) => {
                toast.error(`Error in failedFilesInterval: ${errorPayload}`);
            });
        }, FAILED_FILES_POLL_INTERVAL_MS);

        const queueStatisticsInterval = setInterval(async () => {
            await dispatch(fetchQueueStatistics()).catch((errorPayload) => {
                toast.error(
                    `Error in queueStatisticsInterval: ${errorPayload}`,
                );
            });
        }, QUEUE_STATISTICS_POLL_INTERVAL_MS);

        return () => {
            clearInterval(contentTruncatedFilesInterval);
            clearInterval(attachmentsSkippedFilesInterval);
            clearInterval(failedFilesInterval);
            clearInterval(queueStatisticsInterval);
        };
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    const queryContentTruncatedFiles = () => {
        dispatch(
            updateQuery({
                query: QUERY_CONTENT_TRUNCATED_FILES,
            }),
        );
    };

    const queryAttachmentsSkippedFiles = () => {
        dispatch(
            updateQuery({
                query: QUERY_ATTACHMENTS_SKIPPED_FILES,
            }),
        );
    };

    const queryFailedFiles = () => {
        dispatch(
            updateQuery({
                query: QUERY_FAILED_FILES,
            }),
        );
    };

    const queryFilesNotProcessed = () => {
        dispatch(
            updateQuery({
                query: QUERY_FILES_NOT_PROCESSED,
            }),
        );
    };

    const getActiveSpinnerTooltip = () => {
        const completeEstimateTimestamp =
            queueStatistics.completeEstimateTimestamp;
        let estimatedTimeAddition = "";
        if (queueStatistics.pausedQueuesCount > 0) {
            estimatedTimeAddition = t("header.indexingThrottled", {
                pausedQueuesCount: queueStatistics.pausedQueuesCount,
            });
        } else if (completeEstimateTimestamp != undefined) {
            const nowTimestamp = new Date().getTime() / 1000;
            const completedin = completeEstimateTimestamp - nowTimestamp;

            if (completedin < 60 * 5) {
                // < 5 Minutes
                estimatedTimeAddition = t("header.estimateLessThanFiveMinutes");
            } else if (completedin < 60 * 60 * 3) {
                // < 3 hours
                estimatedTimeAddition = t("header.estimateMinutes", {
                    minutes: Math.ceil(completedin / 60),
                });
            } else if (completedin < 60 * 60 * 52) {
                // < 52 hours
                estimatedTimeAddition = t("header.estimateHours", {
                    hours: Math.ceil(completedin / (60 * 60)),
                });
            } else {
                estimatedTimeAddition = t("header.estimateDays", {
                    days: Math.ceil(completedin / (60 * 60 * 24)),
                });
            }
        }

        return (
            <div>
                <div>
                    {t("header.runningTasksTooltip", {
                        taskCount: queueStatistics.messagesInQueues,
                    })}
                </div>
                <div>{estimatedTimeAddition}</div>
            </div>
        );
    };

    return (
        <Indicator>
            {queueStatistics.messagesInQueues > 0 && (
                <Tooltip title={getActiveSpinnerTooltip()}>
                    <Badge
                        badgeContent={queueStatistics.messagesInQueues}
                        color="primary"
                    >
                        {queueStatistics.pausedQueuesCount > 0 ? (
                            <Box
                                sx={{
                                    position: "relative",
                                    display: "inline-flex",
                                    alignItems: "center",
                                    justifyContent: "center",
                                    cursor: "pointer",
                                }}
                                onClick={queryFilesNotProcessed}
                            >
                                <RunningTasksProgress size="1.5rem" />
                                <Pause
                                    sx={{
                                        position: "absolute",
                                        fontSize: "0.9rem",
                                    }}
                                />
                            </Box>
                        ) : (
                            <RunningTasksProgress
                                size="1.5rem"
                                onClick={queryFilesNotProcessed}
                            />
                        )}
                    </Badge>
                </Tooltip>
            )}
            {contentTruncatedFilesCount > 0 && (
                <Tooltip
                    title={t("header.contentTruncatedTooltip", {
                        contentTruncatedCount: contentTruncatedFilesCount,
                    })}
                >
                    <ErrorCountBadge
                        badgeContent={contentTruncatedFilesCount}
                        color="primary"
                        onClick={queryContentTruncatedFiles}
                    >
                        <ContentCut />
                    </ErrorCountBadge>
                </Tooltip>
            )}
            {attachmentsSkippedFilesCount > 0 && (
                <Tooltip
                    title={t("header.attachmentsSkippedTooltip", {
                        attachmentsSkippedCount: attachmentsSkippedFilesCount,
                    })}
                >
                    <ErrorCountBadge
                        badgeContent={attachmentsSkippedFilesCount}
                        color="primary"
                        onClick={queryAttachmentsSkippedFiles}
                    >
                        <LinkOff />
                    </ErrorCountBadge>
                </Tooltip>
            )}
            {failedBackgroundTaskCount > 0 && (
                <Tooltip
                    title={t("header.failedTasksTooltip", {
                        failedTaskCount: failedBackgroundTaskCount,
                    })}
                >
                    <ErrorCountBadge
                        badgeContent={failedBackgroundTaskCount}
                        color="primary"
                        onClick={queryFailedFiles}
                    >
                        <TaskStatusIcon status={TaskStatus.Error} />
                    </ErrorCountBadge>
                </Tooltip>
            )}
        </Indicator>
    );
};
