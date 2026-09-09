import { AppRegistration, Keyboard } from "@mui/icons-material";
import { Box, Tab, Tabs } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { CardCustomizationPanel } from "./CardCustomizationPanel";
import { KeyboardShortcutsPanel } from "./KeyboardShortcutsPanel";

type CustomizationTab = "card" | "key";

const TAB_SX = {
    minHeight: 48,
    textTransform: "none",
    fontSize: "0.875rem",
};

export const Customization = () => {
    const { t } = useTranslation();
    const [activeTab, setActiveTab] = useState<CustomizationTab>("card");

    return (
        <>
            <Tabs
                value={activeTab}
                onChange={(_, newValue: CustomizationTab) =>
                    setActiveTab(newValue)
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
                    label={t("sideMenu.cardCustomization.title")}
                    iconPosition="start"
                    sx={TAB_SX}
                />
                <Tab
                    value="key"
                    icon={<Keyboard fontSize="small" sx={{ fontSize: 18 }} />}
                    label={t("sideMenu.keyCustomization.title")}
                    iconPosition="start"
                    sx={TAB_SX}
                />
            </Tabs>
            {activeTab === "card" ? (
                <CardCustomizationPanel />
            ) : (
                <Box sx={{ marginLeft: 2 }}>
                    <KeyboardShortcutsPanel />
                </Box>
            )}
        </>
    );
};
