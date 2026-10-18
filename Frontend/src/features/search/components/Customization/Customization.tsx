import { AppRegistration, Bolt, Keyboard } from "@mui/icons-material";
import { Box, Tab, Tabs } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import {
    CustomizationTab,
    getTourCustomizationTab,
} from "@app/tours/tourScene";
import { useTour } from "@app/tours/useTour";

import { AutoActionsPanel } from "./AutoActionsPanel";
import { CardCustomizationPanel } from "./CardCustomizationPanel";
import { KeyboardShortcutsPanel } from "./KeyboardShortcutsPanel";

const TAB_SX = {
    minHeight: 48,
    textTransform: "none",
    fontSize: "0.875rem",
};

export const Customization = () => {
    const { t } = useTranslation();
    const [pickedTab, setPickedTab] = useState<CustomizationTab>("card");
    const { activeTourStepId, isTourActive } = useTour();
    // A tour step points at a section of this panel, and that section is only
    // in the DOM while its tab is the open one. Derived rather than pushed
    // into state by an effect: the tour resolves a step's target in the same
    // tick it activates the step, so a tab switch that waits for an effect
    // arrives one render too late and the step is skipped as missing.
    const activeTab =
        getTourCustomizationTab(isTourActive, activeTourStepId) ?? pickedTab;

    return (
        <>
            <Tabs
                value={activeTab}
                onChange={(_, newValue: CustomizationTab) =>
                    setPickedTab(newValue)
                }
                variant="fullWidth"
                sx={{ minHeight: 48 }}
            >
                <Tab
                    value="card"
                    icon={
                        <AppRegistration
                            fontSize="small"
                            sx={{ fontSize: 18 }}
                        />
                    }
                    label={t("sideMenu.customization.cardTab")}
                    iconPosition="start"
                    sx={TAB_SX}
                />
                <Tab
                    value="actions"
                    icon={<Bolt fontSize="small" sx={{ fontSize: 18 }} />}
                    label={t("sideMenu.customization.actionsTab")}
                    iconPosition="start"
                    sx={TAB_SX}
                />
                <Tab
                    value="key"
                    icon={<Keyboard fontSize="small" sx={{ fontSize: 18 }} />}
                    label={t("sideMenu.customization.keyTab")}
                    iconPosition="start"
                    sx={TAB_SX}
                />
            </Tabs>
            {activeTab === "card" && <CardCustomizationPanel />}
            {activeTab === "actions" && <AutoActionsPanel />}
            {activeTab === "key" && (
                <Box sx={{ marginLeft: 2 }}>
                    <KeyboardShortcutsPanel />
                </Box>
            )}
        </>
    );
};
