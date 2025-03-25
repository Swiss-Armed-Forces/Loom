import { OverallQueuesStats, QueuesApi } from ".";

const queuesApi = new QueuesApi();

export function fetchCount(amount = 1) {
    return new Promise<{ data: number }>((resolve) =>
        window.setTimeout(() => resolve({ data: amount }), 500),
    );
}

export const fetchOverallQueueStatistics =
    async (): Promise<OverallQueuesStats> => {
        return queuesApi.getOverallQueueStatsV1QueuesGet();
    };
