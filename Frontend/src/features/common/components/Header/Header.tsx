import { Inventory, Search } from "@mui/icons-material";
import { AppBar, Box, Tab, Tabs, Toolbar, Tooltip } from "@mui/material";
import { useMediaQuery } from "@mui/material";
import { ComponentProps, ElementType, forwardRef } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation } from "react-router-dom";

import { useAppDispatch } from "@app/hooks";
import { updateQuery } from "@app/slices/searchSlice";
import { DemoModeIndicator } from "@features/common/components/DemoModeIndicator";

import { LoomResponsiveLogo } from "../../branding/LoomResponsiveLogo";

import { ArchiveEncryptionKeyDisplay } from "./ArchiveEncryptionKeyDisplay";
import { BackgroundStatusIndicator } from "./BackgroundStatusIndicator";
import { BurgerMenu } from "./BurgerMenu";
import { GlobalSearchBox } from "./GlobalSearchBox";
import styles from "./Header.module.css";
import { getHeaderStripeConfig } from "./headerStripe";

const TooltipTab = forwardRef<
    HTMLDivElement,
    ComponentProps<typeof Tab> & {
        tooltip: string;
        component?: ElementType;
        to?: string;
    }
>(({ tooltip, ...tabProps }, ref) => (
    <Tooltip title={tooltip}>
        <Tab ref={ref} {...(tabProps as ComponentProps<typeof Tab>)} />
    </Tooltip>
));
TooltipTab.displayName = "TooltipTab";

export const Header = () => {
    const location = useLocation();
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const isMobile = useMediaQuery("(max-width:600px)");
    const isSearchPage =
        location.pathname === "/search" || location.pathname === "/";
    const headerStripe = getHeaderStripeConfig(
        window.location.hostname,
        import.meta.env.MODE === "demo",
    );

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
                headerStripe.enabled
                    ? {
                          backgroundImage: `repeating-linear-gradient(
                              -45deg,
                              ${headerStripe.accentColor} 0 30px,
                              var(--mui-palette-secondary-main) 30px 60px
                          )`,
                          backgroundSize: "84.853px 84.853px",
                          backgroundPosition: "-0.4rem 0",
                      }
                    : {}
            }
        >
            <Toolbar variant="dense" className={styles.toolbar}>
                <DemoModeIndicator />
                {
                    <Link
                        className={styles.headerBranding}
                        data-tour="branding"
                        to={"/"}
                        onClick={() =>
                            dispatch(
                                updateQuery({ query: "", sortField: null }),
                            )
                        }
                    >
                        <LoomResponsiveLogo />
                    </Link>
                }
                {!isMobile && isSearchPage ? (
                    <GlobalSearchBox />
                ) : !isMobile && location.pathname === "/archives" ? (
                    <div style={{ flex: 1 }}>
                        <ArchiveEncryptionKeyDisplay />
                    </div>
                ) : (
                    <div
                        className="globalSearchBoxWrapperPlaceholder"
                        style={{ flex: 1 }}
                    />
                )}
                <BackgroundStatusIndicator />

                <Box className={styles.headerButtons}>
                    <Tabs
                        data-tour="navigation"
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
                            <TooltipTab
                                key={page.route}
                                tooltip={t(`header.${page.route}`)}
                                sx={{
                                    minHeight: "unset",
                                    minWidth: 44,
                                    px: 1,
                                    ":not(&.Mui-selected)": {
                                        color: "white",
                                    },
                                }}
                                icon={page.icon}
                                aria-label={t(`header.${page.route}`)}
                                value={`/${page.route}`}
                                component={Link}
                                to={`/${page.route}`}
                                {...(page.route === "archives"
                                    ? { "data-tour": "archives-tab" }
                                    : {})}
                            />
                        ))}
                    </Tabs>
                    <BurgerMenu></BurgerMenu>
                </Box>
            </Toolbar>
            {isMobile && isSearchPage && (
                <Box sx={{ px: 1, pb: 0.5 }}>
                    <GlobalSearchBox />
                </Box>
            )}
            {isMobile && location.pathname === "/archives" && (
                <Box sx={{ px: 1, pb: 0.5 }}>
                    <ArchiveEncryptionKeyDisplay />
                </Box>
            )}
        </AppBar>
    );
};
