import { Inventory, Search } from "@mui/icons-material";
import { AppBar, Box, Tab, Tabs, Toolbar } from "@mui/material";
import { useMediaQuery } from "@mui/material";
import { useTranslation } from "react-i18next";
import { Link, useLocation } from "react-router-dom";

import { getColorFromString } from "@features/common/utils/helpers";

import { LoomResponsiveLogo } from "../../branding/LoomResponsiveLogo";

import { ArchiveEncryptionKeyDisplay } from "./ArchiveEncryptionKeyDisplay";
import { BackgroundStatusIndicator } from "./BackgroundStatusIndicator";
import { BurgerMenu } from "./BurgerMenu";
import { GlobalSearchBox } from "./GlobalSearchBox";
import styles from "./Header.module.css";
import { ImportArchiveButton } from "./ImportArchiveButton";

export const Header = () => {
    const location = useLocation();
    const { t } = useTranslation();
    const isMobile = useMediaQuery("(max-width:600px)");
    const useAccentColor = window.location.hostname !== "frontend.loom";
    const accentColor = getColorFromString(window.location.hostname);

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
            className={styles.stripedAppHeader}
            color="secondary"
            sx={
                useAccentColor
                    ? {
                          backgroundImage: `repeating-linear-gradient(
                              -45deg,
                              #31312e 0 30px,
                              ${accentColor} 30px 60px
                          )`,
                          backgroundAttachment: "fixed",
                      }
                    : {}
            }
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
                ) : location.pathname === "/archives" ? (
                    <div style={{ flex: 1 }}>
                        <ArchiveEncryptionKeyDisplay />
                    </div>
                ) : (
                    <div className="globalSearchBoxWrapperPlaceholder" />
                )}
                {location.pathname === "/archives" && <ImportArchiveButton />}
                <BackgroundStatusIndicator />
                <Box className={styles.headerButtons}>
                    <Tabs
                        value={
                            location.pathname === "/"
                                ? "/search"
                                : location.pathname
                        }
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
};
