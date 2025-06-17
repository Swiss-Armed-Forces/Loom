import { FC, useEffect } from "react";
import { useAppSelector } from "../../../app/hooks";
import {
    fetchContentTruncatedFiles,
    fetchFailedFiles,
    QUERY_CONTENT_TRUNCATED_FILES,
    QUERY_FAILED_FILES,
    selectContentTruncatedFilesCount,
    selectFailedFilesCount,
    updateQuery,
} from "../searchSlice";
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
import { TaskStatusIcon } from "../../common/components/tasks/TaskStatusIcon";
import { TaskStatus } from "../../common/models/Task";
import { useDispatch } from "react-redux";
import { useTranslation } from "react-i18next";
import { AppDispatch } from "../../../app/store";
import {
    fetchQueueStatistics,
    handleError,
    selectQueuesStatistics,
} from "../../common/commonSlice.ts";
import { ContentCut } from "@mui/icons-material";

const CONTENT_TRUNCATED_FILES_POLL_INTERVAL__MS = 180_000;
const FAILED_FILES_POLL_INTERVAL__MS = 180_000;
const QUEUE_STATISTICS_POLL_INTERVAL__MS = 5_000;

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
    margin-right: 0.5rem;
    cursor: pointer;
`;

export const BackgroundStatusIndicator: FC = () => {
    const contentTruncatedFilesCount = useAppSelector(
        selectContentTruncatedFilesCount,
    );
    const failedBackgroundTaskCount = useAppSelector(selectFailedFilesCount);
    const queueStatistics = useAppSelector(selectQueuesStatistics);
    const { t } = useTranslation();
    const dispatch = useDispatch<AppDispatch>();

    useEffect(() => {
        async function load() {
            await Promise.all([
                dispatch(fetchContentTruncatedFiles()),
                dispatch(fetchFailedFiles()),
                dispatch(fetchQueueStatistics()),
            ]).catch((errorPayload) => {
                dispatch(handleError(errorPayload));
            });
        }
        load();

        const contentTruncatedFilesInterval = setInterval(async () => {
            await dispatch(fetchContentTruncatedFiles()).catch(
                (errorPayload) => {
                    dispatch(handleError(errorPayload));
                },
            );
        }, CONTENT_TRUNCATED_FILES_POLL_INTERVAL__MS);

        const failedFilesInterval = setInterval(async () => {
            await dispatch(fetchFailedFiles()).catch((errorPayload) => {
                dispatch(handleError(errorPayload));
            });
        }, FAILED_FILES_POLL_INTERVAL__MS);

        const queueStatisticsInterval = setInterval(async () => {
            await dispatch(fetchQueueStatistics()).catch((errorPayload) => {
                dispatch(handleError(errorPayload));
            });
        }, QUEUE_STATISTICS_POLL_INTERVAL__MS);

        return () => {
            clearInterval(contentTruncatedFilesInterval);
            clearInterval(failedFilesInterval);
            clearInterval(queueStatisticsInterval);
        };
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    function queryContentTruncatedFiles(): void {
        dispatch(
            updateQuery({
                query: QUERY_CONTENT_TRUNCATED_FILES,
            }),
        );
    }

    function queryFailedFiles(): void {
        dispatch(
            updateQuery({
                query: QUERY_FAILED_FILES,
            }),
        );
    }

    function queryFilesNotProcessed(): void {
        dispatch(
            updateQuery({
                query: QUERY_FILES_NOT_PROCESSED,
            }),
        );
    }

    const getActiveSpinnerTooltip = () => {
        let estimated_time_addition = <span></span>;
        if (queueStatistics.completeEstimateTimestamp != undefined) {
            const now_timestamp = new Date().getTime() / 1000;
            const completed_in =
                queueStatistics.completeEstimateTimestamp - now_timestamp;

            if (completed_in < 60 * 5) {
                // < 5 Minutes
                estimated_time_addition = (
                    <span>{t("header.estimateLessThanFiveMinutes")}</span>
                );
            } else if (completed_in < 60 * 60 * 3) {
                // < 3 hours
                estimated_time_addition = (
                    <span>
                        {t("header.estimateMinutes", {
                            minutes: Math.ceil(completed_in / 60),
                        })}
                    </span>
                );
            } else if (completed_in < 60 * 60 * 52) {
                // < 52 hours
                estimated_time_addition = (
                    <span>
                        {t("header.estimateHours", {
                            hours: Math.ceil(completed_in / (60 * 60)),
                        })}
                    </span>
                );
            } else {
                estimated_time_addition = (
                    <span>
                        {t("header.estimateDays", {
                            days: Math.ceil(completed_in / (60 * 60 * 24)),
                        })}
                    </span>
                );
            }
        }

        return (
            <span>
                {t("header.runningTasksTooltip", {
                    taskCount: queueStatistics.messagesInQueues,
                })}
                <br />
                {estimated_time_addition}
            </span>
        );
    };

    return (
        <Indicator>
            {queueStatistics.messagesInQueues > 0 && (
                <Tooltip title={getActiveSpinnerTooltip()}>
                    <RunningTasksProgress
                        size="1.5rem"
                        onClick={queryFilesNotProcessed}
                    />
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
                        <TaskStatusIcon status={TaskStatus.ERROR} />
                    </ErrorCountBadge>
                </Tooltip>
            )}
        </Indicator>
    );
};
