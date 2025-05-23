/* tslint:disable */
/* eslint-disable */
// @ts-nocheck
/**
 * Loom API
 * No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)
 *
 * The version of the OpenAPI document: 0.1.0
 *
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 */

import * as runtime from "../runtime";
import type { CacheStatisticsEntryModel } from "../models/index";
import {
    CacheStatisticsEntryModelFromJSON,
    CacheStatisticsEntryModelToJSON,
} from "../models/index";

/**
 *
 */
export class CachingApi extends runtime.BaseAPI {
    /**
     * Get Caching Stats
     */
    async getCachingStatsV1CachingGetRaw(
        initOverrides?: RequestInit | runtime.InitOverrideFunction,
    ): Promise<
        runtime.ApiResponse<{ [key: string]: CacheStatisticsEntryModel }>
    > {
        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        const response = await this.request(
            {
                path: `/v1/caching/`,
                method: "GET",
                headers: headerParameters,
                query: queryParameters,
            },
            initOverrides,
        );

        return new runtime.JSONApiResponse(response, (jsonValue) =>
            runtime.mapValues(jsonValue, CacheStatisticsEntryModelFromJSON),
        );
    }

    /**
     * Get Caching Stats
     */
    async getCachingStatsV1CachingGet(
        initOverrides?: RequestInit | runtime.InitOverrideFunction,
    ): Promise<{ [key: string]: CacheStatisticsEntryModel }> {
        const response =
            await this.getCachingStatsV1CachingGetRaw(initOverrides);
        return await response.value();
    }
}
