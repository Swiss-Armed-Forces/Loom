import { AppBar, Box, Button, Toolbar } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link, useLocation } from "react-router-dom";
import { GlobalSearchBox } from "../search/components/GlobalSearchBox";
import { LoomResponsiveLogo } from "./branding/LoomResponsiveLogo";
import styles from "./header.module.css";
import { Inventory, Search } from "@mui/icons-material";
import React from "react";
import { BackgroundStatusIndicator } from "../search/components/BackgroundStatusIndicator";
import { BurgerMenu } from "./components/BurgerMenu";
import { useMediaQuery } from "@mui/material";

export interface Page {
    route: string;
    icon: React.ReactNode;
}

export function Header() {
    const location = useLocation();
    const { t } = useTranslation();
    const isMobile = useMediaQuery("(max-width:600px)");

    const pages: Page[] = [
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
        <AppBar className={styles.appHeader} color="secondary">
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
                    {pages.map((page) => (
                        <Button
                            key={page.route}
                            component={Link}
                            to={`/${page.route}`}
                            startIcon={page.icon}
                            variant={
                                location.pathname == `/${page.route}`
                                    ? "contained"
                                    : "outlined"
                            }
                        >
                            <span className={styles.headerButtonLabel}>
                                {t(`header.${page.route}`)}
                            </span>
                        </Button>
                    ))}
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
