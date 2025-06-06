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
 * @interface MessageError
 */
export interface MessageError {
    /**
     *
     * @type {string}
     * @memberof MessageError
     */
    type?: string;
    /**
     *
     * @type {string}
     * @memberof MessageError
     */
    message: string;
}

/**
 * Check if a given object implements the MessageError interface.
 */
export function instanceOfMessageError(value: object): boolean {
    if (!("message" in value)) return false;
    return true;
}

export function MessageErrorFromJSON(json: any): MessageError {
    return MessageErrorFromJSONTyped(json, false);
}

export function MessageErrorFromJSONTyped(
    json: any,
    ignoreDiscriminator: boolean,
): MessageError {
    if (json == null) {
        return json;
    }
    return {
        type: json["type"] == null ? undefined : json["type"],
        message: json["message"],
    };
}

export function MessageErrorToJSON(value?: MessageError | null): any {
    if (value == null) {
        return value;
    }
    return {
        type: value["type"],
        message: value["message"],
    };
}
