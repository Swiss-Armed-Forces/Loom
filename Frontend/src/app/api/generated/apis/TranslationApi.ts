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
import type {
    HTTPValidationError,
    LibretranslateSupportedLanguages,
    TranslateAllRequest,
} from "../models/index";
import {
    HTTPValidationErrorFromJSON,
    HTTPValidationErrorToJSON,
    LibretranslateSupportedLanguagesFromJSON,
    LibretranslateSupportedLanguagesToJSON,
    TranslateAllRequestFromJSON,
    TranslateAllRequestToJSON,
} from "../models/index";

export interface TranslateFilesOnDemandV1FilesTranslationPostRequest {
    translateAllRequest: TranslateAllRequest;
}

/**
 *
 */
export class TranslationApi extends runtime.BaseAPI {
    /**
     * Get Supported Languages
     */
    async getSupportedLanguagesV1FilesTranslationLanguagesGetRaw(
        initOverrides?: RequestInit | runtime.InitOverrideFunction,
    ): Promise<runtime.ApiResponse<Array<LibretranslateSupportedLanguages>>> {
        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        const response = await this.request(
            {
                path: `/v1/files/translation/languages`,
                method: "GET",
                headers: headerParameters,
                query: queryParameters,
            },
            initOverrides,
        );

        return new runtime.JSONApiResponse(response, (jsonValue) =>
            jsonValue.map(LibretranslateSupportedLanguagesFromJSON),
        );
    }

    /**
     * Get Supported Languages
     */
    async getSupportedLanguagesV1FilesTranslationLanguagesGet(
        initOverrides?: RequestInit | runtime.InitOverrideFunction,
    ): Promise<Array<LibretranslateSupportedLanguages>> {
        const response =
            await this.getSupportedLanguagesV1FilesTranslationLanguagesGetRaw(
                initOverrides,
            );
        return await response.value();
    }

    /**
     * Translate Files On Demand
     */
    async translateFilesOnDemandV1FilesTranslationPostRaw(
        requestParameters: TranslateFilesOnDemandV1FilesTranslationPostRequest,
        initOverrides?: RequestInit | runtime.InitOverrideFunction,
    ): Promise<runtime.ApiResponse<any>> {
        if (requestParameters["translateAllRequest"] == null) {
            throw new runtime.RequiredError(
                "translateAllRequest",
                'Required parameter "translateAllRequest" was null or undefined when calling translateFilesOnDemandV1FilesTranslationPost().',
            );
        }

        const queryParameters: any = {};

        const headerParameters: runtime.HTTPHeaders = {};

        headerParameters["Content-Type"] = "application/json";

        const response = await this.request(
            {
                path: `/v1/files/translation/`,
                method: "POST",
                headers: headerParameters,
                query: queryParameters,
                body: TranslateAllRequestToJSON(
                    requestParameters["translateAllRequest"],
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
     * Translate Files On Demand
     */
    async translateFilesOnDemandV1FilesTranslationPost(
        requestParameters: TranslateFilesOnDemandV1FilesTranslationPostRequest,
        initOverrides?: RequestInit | runtime.InitOverrideFunction,
    ): Promise<any> {
        const response =
            await this.translateFilesOnDemandV1FilesTranslationPostRaw(
                requestParameters,
                initOverrides,
            );
        return await response.value();
    }
}
