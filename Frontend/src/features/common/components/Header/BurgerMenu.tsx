import {
    ApiOutlined,
    CloudCircleOutlined,
    MailOutlineOutlined,
    SmartToyOutlined,
    TaskOutlined,
    InfoOutlined,
    ExpandOutlined,
    PrecisionManufacturingOutlined,
    FindInPageOutlined,
    PictureAsPdfOutlined,
    InsightsOutlined,
    WhatshotOutlined,
    Menu as MenuIcon,
    CloudUploadOutlined,
    KeyOutlined,
    StorageOutlined,
    SearchOutlined,
    QueueOutlined,
} from "@mui/icons-material";
import { IconButton, Menu, MenuItem } from "@mui/material";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch } from "@app/hooks";
import { openDialog } from "@app/slices/commonSlice";
import { useTour } from "@app/tours/useTour";
import { notifyIfUnavailableInDemoMode } from "@features/common/demoModeUnavailableAction";
import {
    apiHost,
    elasticVueHost,
    flowerHost,
    grafanaHost,
    s3Host,
    openWebuifrontendHost,
    prometheusHost,
    rabbitHost,
    roundcubeHost,
    rspamdHost,
    traefikHost,
    redisInsightHost,
    tikaHost,
    ollamaHost,
    elasticSearchHost,
    gotenbergHost,
    seaweedfsHost,
} from "@features/common/urls";
import { DemoUnavailableFeature } from "@features/common/utils/demoMode";
import { DialogType } from "@features/common/utils/enums";

export interface Page {
    route: string;
    icon: React.ReactNode;
}

export const BurgerMenu = () => {
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const { activeTourStepId, isTourActive } = useTour();
    const buttonRef = useRef<HTMLButtonElement>(null);

    useEffect(() => {
        if (!isTourActive) return;
        if (activeTourStepId === "menu" && buttonRef.current) {
            setAnchorEl(buttonRef.current);
        } else {
            setAnchorEl(null);
        }
    }, [isTourActive, activeTourStepId]);

    const handleAboutClick = () => {
        dispatch(openDialog({ id: "", type: DialogType.About }));
    };

    const handleMenuOpen = (event: React.MouseEvent<HTMLButtonElement>) => {
        setAnchorEl(event.currentTarget);
    };

    const handleMenuClose = () => {
        setAnchorEl(null);
    };

    const handleServiceClick = (event: React.MouseEvent<HTMLAnchorElement>) => {
        if (
            notifyIfUnavailableInDemoMode(
                DemoUnavailableFeature.BackendServices,
            )
        )
            event.preventDefault();
        handleMenuClose();
    };

    const menuItems = [
        {
            link: openWebuifrontendHost,
            text: "Open WebUI",
            icon: <SmartToyOutlined />,
            params: { "temporary-chat": "true" },
        },
        {
            link: roundcubeHost,
            text: "Roundcube",
            icon: <MailOutlineOutlined />,
        },
        {
            link: seaweedfsHost,
            text: "SeaweedFS",
            icon: <StorageOutlined />,
        },
        {
            link: apiHost,
            text: "Api",
            icon: <ApiOutlined />,
        },
        {
            link: s3Host,
            text: "S3",
            icon: <CloudUploadOutlined />,
        },
        {
            link: flowerHost,
            text: "Flower",
            icon: <TaskOutlined />,
        },
        {
            link: rabbitHost,
            text: "RabbitMQ",
            icon: <QueueOutlined />,
        },
        {
            link: elasticVueHost,
            text: "ElasticVue",
            icon: <SearchOutlined />,
        },
        {
            link: rspamdHost,
            text: "Rspamd",
            icon: <MailOutlineOutlined />,
        },
        {
            link: redisInsightHost,
            text: "Redis",
            icon: <KeyOutlined />,
        },
        {
            link: prometheusHost,
            text: "Prometheus",
            icon: <WhatshotOutlined />,
        },
        {
            link: grafanaHost,
            text: "Grafana",
            icon: <InsightsOutlined />,
        },
        {
            link: tikaHost,
            text: "Apache Tika",
            icon: <ExpandOutlined />,
        },
        {
            link: gotenbergHost,
            text: "Gotenberg",
            icon: <PictureAsPdfOutlined />,
        },
        {
            link: ollamaHost,
            text: "Ollama",
            icon: <PrecisionManufacturingOutlined />,
        },
        {
            link: elasticSearchHost,
            text: "ElasticSearch",
            icon: <FindInPageOutlined />,
        },
        {
            link: traefikHost,
            text: "Traefik",
            icon: <CloudCircleOutlined />,
        },
    ];

    return (
        <div data-tour="menu">
            <IconButton
                ref={buttonRef}
                sx={{
                    backgroundColor: "rgba(0, 0, 0, 0.75)",
                    "&:hover": {
                        backgroundColor: "rgba(0, 0, 0, 0.85)",
                    },
                }}
                edge="start"
                color="inherit"
                aria-label="menu"
                onClick={handleMenuOpen}
            >
                <MenuIcon />
            </IconButton>
            <Menu
                id="simple-menu"
                anchorEl={anchorEl}
                keepMounted
                open={Boolean(anchorEl)}
                onClose={handleMenuClose}
                disablePortal={isTourActive && activeTourStepId === "menu"}
            >
                {menuItems.map((item, index) => (
                    <MenuItem
                        component="a"
                        href={(() => {
                            const url = new URL(item.link.toString());
                            if (item.params) {
                                Object.entries(item.params).forEach(([k, v]) =>
                                    url.searchParams.set(k, v),
                                );
                            }
                            return url.toString();
                        })()}
                        target="_blank"
                        rel="noopener noreferrer"
                        key={index}
                        onClick={handleServiceClick}
                    >
                        {item.icon}
                        {item.text}
                    </MenuItem>
                ))}
                <MenuItem
                    component="a"
                    data-tour="menu-about"
                    onClick={handleAboutClick}
                >
                    <InfoOutlined />
                    {t("about.title")}
                </MenuItem>
            </Menu>
        </div>
    );
};
