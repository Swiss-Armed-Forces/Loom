import { t } from "i18next";
import { toast } from "react-toastify";

import {
    DemoUnavailableFeature,
    type DemoUnavailableFeature as DemoUnavailableFeatureType,
} from "@features/common/utils/demoMode";

const messageKeys: Record<DemoUnavailableFeatureType, string> = {
    [DemoUnavailableFeature.ArchiveImport]:
        "demoMode.unavailable.archiveImport",
    [DemoUnavailableFeature.BackendServices]:
        "demoMode.unavailable.backendServices",
    [DemoUnavailableFeature.FileUpload]: "demoMode.unavailable.fileUpload",
    [DemoUnavailableFeature.TaskDetails]: "demoMode.unavailable.taskDetails",
};

export const notifyIfUnavailableInDemoMode = (
    feature: DemoUnavailableFeatureType,
): boolean => {
    toast.info(t(messageKeys[feature]), {
        toastId: `demo-unavailable-${feature}`,
    });
    return true;
};
