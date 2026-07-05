import { Close } from "@mui/icons-material";
import { IconButton, Tab, Tabs } from "@mui/material";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    RightSidebarTab,
    selectRightSidebarOpen,
    selectRightSidebarTab,
    setRightSidebarTab,
    toggleRightSidebar,
} from "@app/slices/searchSlice";
import { Chatbot } from "@features/search/components/ChatMenu/Chatbot";
import { StatisticsView } from "@features/search/views/Statistics/StatisticsView";

import styles from "./RightSidebar.module.css";

export const RightSidebar = () => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();
    const isOpen = useAppSelector(selectRightSidebarOpen);
    const activeTab = useAppSelector(selectRightSidebarTab);

    return (
        <div
            className={`${styles.rightSidebar} ${!isOpen ? styles.closed : ""}`}
        >
            {isOpen && (
                <>
                    <div className={styles.header}>
                        <Tabs
                            className={styles.tabs}
                            value={activeTab}
                            onChange={(_, tab: RightSidebarTab) =>
                                dispatch(setRightSidebarTab(tab))
                            }
                            textColor="inherit"
                        >
                            <Tab
                                value={RightSidebarTab.STATISTICS}
                                label={t("toolbar.views.statistics")}
                            />
                            <Tab value={RightSidebarTab.CHAT} label="Chatbot" />
                        </Tabs>
                        <IconButton
                            size="small"
                            onClick={() => dispatch(toggleRightSidebar())}
                            sx={{ mr: 0.5 }}
                        >
                            <Close fontSize="small" />
                        </IconButton>
                    </div>
                    <div className={styles.content}>
                        {activeTab === RightSidebarTab.STATISTICS ? (
                            <StatisticsView />
                        ) : (
                            <Chatbot />
                        )}
                    </div>
                </>
            )}
        </div>
    );
};
