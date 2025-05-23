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
import type { HTTPValidationError, IndexAllRequest } from "../models/index";
import {
    HTTPValidationErrorFromJSON,
    HTTPValidationErrorToJSON,
    IndexAllRequestFromJSON,
    IndexAllRequestToJSON,
} from "../models/index";

export interface IndexFilesOnDemandV1FilesIndexPostRequest {
    indexAllRequest: IndexAllRequest;
}

/**
 *
 */
export class IndexApi extends runtime.BaseAPI {
    /**
     * Index Files On Demand
     */
    async indexFilesOnDemandV1FilesIndexPostRaw(
        requestParameters: IndexFilesOnDemandV1FilesIndexPostRequest,
        initOverrides?: RequestInit | runtime.InitOverrideFunction,
    ): Promise<runtime.ApiResponse<any>> {
        if (requestParameters["indexAllRequest"] == null) {
            throw new runtime.RequiredError(
                "indexAllRequest",
                'Required parameter "indexAllRequest" was null or undefined when calling indexFilesOnDemandV1FilesIndexPost().',
            );
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters["Content-Type"] = "application/json";

        const response = await this.request(
            {
                path: `/v1/files/index/`,
                method: "POST",
                headers: headerParameters,
                query: queryParameters,
                body: IndexAllRequestToJSON(
                    requestParameters["indexAllRequest"],
                ),
            },
            initOverrides,
        );

        if (this.isJsonMime(response.headers.get("content-type"))) {
            return new runtime.JSONApiResponse<any>(response);
        } else {
            return new runtime.TextApiResponse(response) as any;
        }
    }

    /**
     * Index Files On Demand
     */
    async indexFilesOnDemandV1FilesIndexPost(
        requestParameters: IndexFilesOnDemandV1FilesIndexPostRequest,
        initOverrides?: RequestInit | runtime.InitOverrideFunction,
    ): Promise<any> {
        const response = await this.indexFilesOnDemandV1FilesIndexPostRaw(
            requestParameters,
            initOverrides,
        );
        return await response.value();
    }
}
