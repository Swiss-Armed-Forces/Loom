import { AppBar, Box, Tab, Tabs, Toolbar } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link, useLocation } from "react-router-dom";
import { GlobalSearchBox } from "../search/components/GlobalSearchBox";
import { LoomResponsiveLogo } from "./branding/LoomResponsiveLogo";
import styles from "./header.module.css";
import { Inventory, Search } from "@mui/icons-material";
import { BackgroundStatusIndicator } from "../search/components/BackgroundStatusIndicator";
import { BurgerMenu } from "./components/BurgerMenu";
import { useMediaQuery } from "@mui/material";

export function Header() {
    const location = useLocation();
    const { t } = useTranslation();
    const isMobile = useMediaQuery("(max-width:600px)");
    const useStripedNavbar = window.location.hostname !== "frontend.loom";

    const pages = [
        {
            route: "search",
            icon: <Search />,
        },
        {
            route: "archives",
            icon: <Inventory />,
        },
    ];

    return (
        <AppBar
            className={
                useStripedNavbar ? styles.stripedAppHeader : styles.appHeader
            }
            color="secondary"
        >
            <Toolbar className={styles.toolbar}>
                {
                    <Link className={styles.headerBranding} to={"/"}>
                        <LoomResponsiveLogo />
                    </Link>
                }
                {!isMobile &&
                (location.pathname === "/search" ||
                    location.pathname === "/") ? (
                    <GlobalSearchBox />
                ) : (
                    <div className="globalSearchBoxWrapperPlaceholder" />
                )}
                <BackgroundStatusIndicator />
                <Box className={styles.headerButtons}>
                    <Tabs
                        value={location.pathname}
                        aria-label="loom tabs"
                        sx={{
                            backgroundColor: "rgba(0,0,0,0.75)",
                            borderRadius: "0.3rem",
                            minHeight: "unset",
                        }}
                    >
                        {pages.map((page) => (
                            <Tab
                                sx={{
                                    minHeight: "unset",
                                    ":not(&.Mui-selected)": {
                                        color: "white",
                                    },
                                }}
                                icon={page.icon}
                                iconPosition="start"
                                label={
                                    <span className={styles.headerButtonLabel}>
                                        {t(`header.${page.route}`)}
                                    </span>
                                }
                                key={page.route}
                                value={`/${page.route}`}
                                component={Link}
                                to={`/${page.route}`}
                            />
                        ))}
                    </Tabs>
                    <BurgerMenu></BurgerMenu>
                </Box>
            </Toolbar>
            {isMobile &&
            (location.pathname === "/search" || location.pathname === "/") ? (
                <Toolbar className={styles.toolbar}>
                    <GlobalSearchBox />
                </Toolbar>
            ) : null}
        </AppBar>
    );
}
