import { describe, expect, it } from "vitest";

import { getColorFromString } from "@features/common/utils/helpers";

import {
    DEMO_HEADER_STRIPE_COLOR,
    getHeaderStripeConfig,
} from "./headerStripe";

describe("header stripe configuration", () => {
    it.each([
        "loom-1c8449.gitlab.io",
        "localhost",
        "mr-preview.example.com",
        "frontend.loom",
    ])("uses the fixed demo stripe color on %s", (hostname) => {
        expect(getHeaderStripeConfig(hostname, true)).toEqual({
            accentColor: DEMO_HEADER_STRIPE_COLOR,
            enabled: true,
        });
    });

    it("keeps the production hostname unstriped", () => {
        expect(getHeaderStripeConfig("frontend.loom", false)).toEqual({
            accentColor: getColorFromString("frontend.loom"),
            enabled: false,
        });
    });

    it("keeps hostname-derived colors for other regular deployments", () => {
        const hostname = "review.example.com";

        expect(getHeaderStripeConfig(hostname, false)).toEqual({
            accentColor: getColorFromString(hostname),
            enabled: true,
        });
    });
});
