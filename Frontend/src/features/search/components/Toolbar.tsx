import { Chat, BarChart, Folder, ViewStream } from "@mui/icons-material";
import {
    Button,
    ToggleButton,
    ToggleButtonGroup,
    useMediaQuery,
} from "@mui/material";
import styles from "./Toolbar.module.css";
import {
    SearchView,
    selectActiveSearchView,
    setChatbotOpen,
    setSearchView,
} from "../searchSlice.ts";
import { useAppDispatch, useAppSelector } from "../../../app/hooks.ts";
import { useTranslation } from "react-i18next";

type SearchViewListIcon = {
    [key in SearchView]: {
        icon: React.ReactNode;
    };
};

export const Toolbar = () => {
    const dispatch = useAppDispatch();
    const activeSearchView = useAppSelector(selectActiveSearchView);
    const { t } = useTranslation();
    const chatbotOpen = useAppSelector((state) => state.search.chatbotOpen);
    const isMobile = useMediaQuery("(max-width:600px)");

    const toggleChatbot = () => {
        dispatch(setChatbotOpen(!chatbotOpen));
    };

    const searchViews: SearchViewListIcon = {
        [SearchView.DETAILED]: { icon: <ViewStream /> },
        [SearchView.FOLDER]: { icon: <Folder /> },
        [SearchView.STATISTICS]: { icon: <BarChart /> },
    };

    const handleChangeView = (
        _: React.MouseEvent<HTMLElement>,
        newViewType: SearchView | null,
    ) => {
        if (newViewType !== null) {
            dispatch(setSearchView(newViewType));
        }
    };

    return (
        <div
            className={styles.toolbar}
            style={{ display: "flex", alignItems: "center " }}
        >
            <ToggleButtonGroup
                size="small"
                value={activeSearchView}
                onChange={handleChangeView}
                exclusive
                aria-label="change view type"
            >
                {Object.entries(searchViews).map(([key, val]) => (
                    <ToggleButton
                        value={key as SearchView}
                        key={key}
                        aria-label={"change-view-to-" + key}
                        className={styles.toggleButton}
                    >
                        {val.icon}
                        {!isMobile && t("toolbar.views." + key)}
                    </ToggleButton>
                ))}
            </ToggleButtonGroup>
            <Button
                startIcon={<Chat />}
                variant="contained"
                onClick={toggleChatbot}
            >
                {!isMobile && "Chatbot"}
            </Button>
        </div>
    );
};
