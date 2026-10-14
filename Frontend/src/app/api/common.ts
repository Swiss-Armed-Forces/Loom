import { apiConfiguration } from "./apiConfiguration";
import { AboutApi, CompleteEstimateApi, QueuesApi } from "./generated/apis";
import {
    AboutInfo,
    CompleteEstimateResult,
    QueuesStats,
} from "./generated/models";

const queuesApi = new QueuesApi(apiConfiguration);
const completeEstimateApi = new CompleteEstimateApi(apiConfiguration);
const aboutApi = new AboutApi(apiConfiguration);

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
        return completeEstimateApi.getCompleteEstimateV1CompleteEstimateGet();
    };

export const fetchAbout = async (): Promise<AboutInfo> => {
    return aboutApi.getAboutV1AboutGet();
};
