import { CompleteEstimateApi, QueuesApi } from "./generated/apis";
import { CompleteEstimateResult, QueuesStats } from "./generated/models";

const queuesApi = new QueuesApi();

export const fetchCount = (amount = 1) => {
    return new Promise<{ data: number }>((resolve) =>
        window.setTimeout(() => {
            resolve({ data: amount });
        }, 500),
    );
};

export const fetchQueueStats = async (): Promise<QueuesStats> => {
    return queuesApi.getOverallQueueStatsV1QueuesStatsGet();
};

export const fetchCompleteEstimate =
    async (): Promise<CompleteEstimateResult> => {
        return new CompleteEstimateApi().getCompleteEstimateV1CompleteEstimateGet();
    };
