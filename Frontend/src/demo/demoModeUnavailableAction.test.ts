import { beforeEach, describe, expect, it, vi } from "vitest";

import { notifyIfUnavailableInDemoMode as productionNotification } from "@features/common/demoModeUnavailableAction";
import { DemoUnavailableFeature } from "@features/common/utils/demoMode";

import { notifyIfUnavailableInDemoMode } from "./demoModeUnavailableAction";

const toastInfo = vi.hoisted(() => vi.fn());
const translations = vi.hoisted<Record<string, string>>(() => ({
    "demoMode.unavailable.fileUpload":
        "File uploads aren't available in demo mode. Use a full Loom deployment to process your own files.",
    "demoMode.unavailable.archiveImport":
        "Archive imports aren't available in demo mode. Use a full Loom deployment to import Loom archives.",
    "demoMode.unavailable.backendServices":
        "Backend services aren't available in demo mode. Use a full Loom deployment to access them.",
    "demoMode.unavailable.taskDetails":
        "Task execution details aren't available because demo mode has no Flower service.",
}));

vi.mock("i18next", () => ({
    t: (key: string) => translations[key] ?? key,
}));

vi.mock("react-toastify", () => ({
    toast: { info: toastInfo },
}));

describe("demo unavailable action notifications", () => {
    beforeEach(() => toastInfo.mockClear());

    it.each([
        [
            DemoUnavailableFeature.FileUpload,
            "File uploads aren't available in demo mode. Use a full Loom deployment to process your own files.",
        ],
        [
            DemoUnavailableFeature.ArchiveImport,
            "Archive imports aren't available in demo mode. Use a full Loom deployment to import Loom archives.",
        ],
        [
            DemoUnavailableFeature.BackendServices,
            "Backend services aren't available in demo mode. Use a full Loom deployment to access them.",
        ],
        [
            DemoUnavailableFeature.TaskDetails,
            "Task execution details aren't available because demo mode has no Flower service.",
        ],
    ])("shows a deduplicated message for %s", (feature, message) => {
        expect(notifyIfUnavailableInDemoMode(feature)).toBe(true);
        expect(toastInfo).toHaveBeenCalledWith(message, {
            toastId: `demo-unavailable-${feature}`,
        });
    });

    it("does not block or notify in the production adapter", () => {
        expect(productionNotification(DemoUnavailableFeature.FileUpload)).toBe(
            false,
        );
        expect(toastInfo).not.toHaveBeenCalled();
    });
});
