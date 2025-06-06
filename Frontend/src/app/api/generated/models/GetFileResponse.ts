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

import { mapValues } from "../runtime";
import type { GetFileLanguageTranslations } from "./GetFileLanguageTranslations";
import {
    GetFileLanguageTranslationsFromJSON,
    GetFileLanguageTranslationsFromJSONTyped,
    GetFileLanguageTranslationsToJSON,
} from "./GetFileLanguageTranslations";

/**
 *
 * @export
 * @interface GetFileResponse
 */
export interface GetFileResponse {
    /**
     *
     * @type {string}
     * @memberof GetFileResponse
     */
    fileId: string;
    /**
     *
     * @type {{ [key: string]: any; }}
     * @memberof GetFileResponse
     */
    highlight?: { [key: string]: any };
    /**
     *
     * @type {string}
     * @memberof GetFileResponse
     */
    content: string;
    /**
     *
     * @type {string}
     * @memberof GetFileResponse
     */
    name: string;
    /**
     *
     * @type {Array<GetFileLanguageTranslations>}
     * @memberof GetFileResponse
     */
    libretranslateLanguageTranslations: Array<GetFileLanguageTranslations>;
    /**
     *
     * @type {string}
     * @memberof GetFileResponse
     */
    raw: string;
    /**
     *
     * @type {string}
     * @memberof GetFileResponse
     */
    summary?: string;
}

/**
 * Check if a given object implements the GetFileResponse interface.
 */
export function instanceOfGetFileResponse(value: object): boolean {
    if (!("fileId" in value)) return false;
    if (!("content" in value)) return false;
    if (!("name" in value)) return false;
    if (!("libretranslateLanguageTranslations" in value)) return false;
    if (!("raw" in value)) return false;
    return true;
}

export function GetFileResponseFromJSON(json: any): GetFileResponse {
    return GetFileResponseFromJSONTyped(json, false);
}

export function GetFileResponseFromJSONTyped(
    json: any,
    ignoreDiscriminator: boolean,
): GetFileResponse {
    if (json == null) {
        return json;
    }
    return {
        fileId: json["file_id"],
        highlight: json["highlight"] == null ? undefined : json["highlight"],
        content: json["content"],
        name: json["name"],
        libretranslateLanguageTranslations: (
            json["libretranslate_language_translations"] as Array<any>
        ).map(GetFileLanguageTranslationsFromJSON),
        raw: json["raw"],
        summary: json["summary"] == null ? undefined : json["summary"],
    };
}

export function GetFileResponseToJSON(value?: GetFileResponse | null): any {
    if (value == null) {
        return value;
    }
    return {
        file_id: value["fileId"],
        highlight: value["highlight"],
        content: value["content"],
        name: value["name"],
        libretranslate_language_translations: (
            value["libretranslateLanguageTranslations"] as Array<any>
        ).map(GetFileLanguageTranslationsToJSON),
        raw: value["raw"],
        summary: value["summary"],
    };
}
