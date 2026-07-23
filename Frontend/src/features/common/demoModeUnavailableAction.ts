import { type DemoUnavailableFeature } from "./utils/demoMode";

export const notifyIfUnavailableInDemoMode = (
    feature: DemoUnavailableFeature,
): boolean => {
    void feature;
    return false;
};
