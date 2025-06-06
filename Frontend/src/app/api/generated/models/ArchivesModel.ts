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
import type { ArchiveHit } from "./ArchiveHit";
import {
    ArchiveHitFromJSON,
    ArchiveHitFromJSONTyped,
    ArchiveHitToJSON,
} from "./ArchiveHit";

/**
 *
 * @export
 * @interface ArchivesModel
 */
export interface ArchivesModel {
    /**
     *
     * @type {boolean}
     * @memberof ArchivesModel
     */
    clean: boolean;
    /**
     *
     * @type {Array<ArchiveHit>}
     * @memberof ArchivesModel
     */
    hits: Array<ArchiveHit>;
    /**
     *
     * @type {number}
     * @memberof ArchivesModel
     */
    total: number;
    /**
     *
     * @type {number}
     * @memberof ArchivesModel
     */
    found: number;
    /**
     *
     * @type {boolean}
     * @memberof ArchivesModel
     */
    hasMore: boolean;
    /**
     *
     * @type {number}
     * @memberof ArchivesModel
     */
    currentPage: number;
}

/**
 * Check if a given object implements the ArchivesModel interface.
 */
export function instanceOfArchivesModel(value: object): boolean {
    if (!("clean" in value)) return false;
    if (!("hits" in value)) return false;
    if (!("total" in value)) return false;
    if (!("found" in value)) return false;
    if (!("hasMore" in value)) return false;
    if (!("currentPage" in value)) return false;
    return true;
}

export function ArchivesModelFromJSON(json: any): ArchivesModel {
    return ArchivesModelFromJSONTyped(json, false);
}

export function ArchivesModelFromJSONTyped(
    json: any,
    ignoreDiscriminator: boolean,
): ArchivesModel {
    if (json == null) {
        return json;
    }
    return {
        clean: json["clean"],
        hits: (json["hits"] as Array<any>).map(ArchiveHitFromJSON),
        total: json["total"],
        found: json["found"],
        hasMore: json["hasMore"],
        currentPage: json["currentPage"],
    };
}

export function ArchivesModelToJSON(value?: ArchivesModel | null): any {
    if (value == null) {
        return value;
    }
    return {
        clean: value["clean"],
        hits: (value["hits"] as Array<any>).map(ArchiveHitToJSON),
        total: value["total"],
        found: value["found"],
        hasMore: value["hasMore"],
        currentPage: value["currentPage"],
    };
}
