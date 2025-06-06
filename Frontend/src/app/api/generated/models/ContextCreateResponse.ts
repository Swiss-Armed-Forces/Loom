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
/**
 *
 * @export
 * @interface ContextCreateResponse
 */
export interface ContextCreateResponse {
    /**
     *
     * @type {string}
     * @memberof ContextCreateResponse
     */
    contextId: string;
}

/**
 * Check if a given object implements the ContextCreateResponse interface.
 */
export function instanceOfContextCreateResponse(value: object): boolean {
    if (!("contextId" in value)) return false;
    return true;
}

export function ContextCreateResponseFromJSON(
    json: any,
): ContextCreateResponse {
    return ContextCreateResponseFromJSONTyped(json, false);
}

export function ContextCreateResponseFromJSONTyped(
    json: any,
    ignoreDiscriminator: boolean,
): ContextCreateResponse {
    if (json == null) {
        return json;
    }
    return {
        contextId: json["context_id"],
    };
}

export function ContextCreateResponseToJSON(
    value?: ContextCreateResponse | null,
): any {
    if (value == null) {
        return value;
    }
    return {
        context_id: value["contextId"],
    };
}
