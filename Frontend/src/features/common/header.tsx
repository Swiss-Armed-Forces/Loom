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

export interface Page {
    route: string;
    icon: React.ReactNode;
}

export function Header() {
    const location = useLocation();
    const { t } = useTranslation();
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
                        <LoomResponsiveLogo color={"#FFBF00"} />
                    </Link>
                }
                {location.pathname === "/search" ||
                location.pathname === "/" ? (
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
                            {t(`header.${page.route}`)}
                        </Button>
                    ))}
                    <BurgerMenu></BurgerMenu>
                </Box>
            </Toolbar>
        </AppBar>
    );
}
