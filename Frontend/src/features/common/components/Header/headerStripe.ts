import { getColorFromString } from "@features/common/utils/helpers";

export const DEMO_HEADER_STRIPE_COLOR =
    "var(--mui-palette-error-main, #ff4444)";

interface HeaderStripeConfig {
    accentColor: string;
    enabled: boolean;
}

export const getHeaderStripeConfig = (
    hostname: string,
    isDemo: boolean,
): HeaderStripeConfig => ({
    accentColor: isDemo
        ? DEMO_HEADER_STRIPE_COLOR
        : getColorFromString(hostname),
    enabled: isDemo || hostname !== "frontend.loom",
});
