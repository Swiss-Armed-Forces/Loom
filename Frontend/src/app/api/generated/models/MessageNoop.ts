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
 * @interface MessageNoop
 */
export interface MessageNoop {
    /**
     *
     * @type {string}
     * @memberof MessageNoop
     */
    type?: string;
}

/**
 * Check if a given object implements the MessageNoop interface.
 */
export function instanceOfMessageNoop(value: object): boolean {
    return true;
}

export function MessageNoopFromJSON(json: any): MessageNoop {
    return MessageNoopFromJSONTyped(json, false);
}

export function MessageNoopFromJSONTyped(
    json: any,
    ignoreDiscriminator: boolean,
): MessageNoop {
    if (json == null) {
        return json;
    }
    return {
        type: json["type"] == null ? undefined : json["type"],
    };
}

export function MessageNoopToJSON(value?: MessageNoop | null): any {
    if (value == null) {
        return value;
    }
    return {
        type: value["type"],
    };
}
