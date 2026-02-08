import { IconButton, Menu, MenuItem } from "@mui/material";
import { useState } from "react";
import MenuIcon from "@mui/icons-material/Menu";
import QueueOutlinedIcon from "@mui/icons-material/QueueOutlined";
import SearchOutlinedIcon from "@mui/icons-material/Search";
export interface Page {
    route: string;
    icon: React.ReactNode;
}
import {
    ApiOutlined,
    CloudCircleOutlined,
    MailOutlineOutlined,
    SmartToyOutlined,
    TaskOutlined,
    InfoOutlined,
    StorageOutlined,
    ExpandOutlined,
    PrecisionManufacturingOutlined,
    FindInPageOutlined,
    PictureAsPdfOutlined,
    InsightsOutlined,
    WhatshotOutlined,
    DataObjectOutlined,
    TranslateOutlined,
    DriveFolderUploadOutlined,
} from "@mui/icons-material";
import {
    apiHost,
    elasticVueHost,
    flowerHost,
    grafanaHost,
    translateHost,
    minioHost,
    mongoWebHost,
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
} from "../urls";
import { useTranslation } from "react-i18next";
import { AboutDialog } from "./AboutDialog";

export function BurgerMenu() {
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const [openAboutDialog, setOpenAboutDialog] = useState(false);
    const { t } = useTranslation();

    const handleMenuOpen = (
        event: React.MouseEvent<HTMLButtonElement, MouseEvent>,
    ) => {
        setAnchorEl(event.currentTarget);
    };

    const handleMenuClose = () => {
        setAnchorEl(null);
    };

    const menuItems = [
        {
            link: translateHost,
            text: "Translate",
            icon: <TranslateOutlined />,
        },
        {
            link: openWebuifrontendHost,
            text: "Open WebUI",
            icon: <SmartToyOutlined />,
        },
        {
            link: roundcubeHost,
            text: "Roundcube",
            icon: <MailOutlineOutlined />,
        },
        {
            link: minioHost,
            text: "Minio",
            icon: <DriveFolderUploadOutlined />,
        },
        {
            link: apiHost,
            text: "Api",
            icon: <ApiOutlined />,
        },
        {
            link: flowerHost,
            text: "Flower",
            icon: <TaskOutlined />,
        },
        {
            link: rabbitHost,
            text: "RabbitMQ",
            icon: <QueueOutlinedIcon />,
        },
        {
            link: elasticVueHost,
            text: "ElasticVue",
            icon: <SearchOutlinedIcon />,
        },
        {
            link: mongoWebHost,
            text: "MongoDB",
            icon: <DataObjectOutlined />,
        },
        {
            link: rspamdHost,
            text: "Rspamd",
            icon: <MailOutlineOutlined />,
        },
        {
            link: redisInsightHost,
            text: "Redis",
            icon: <StorageOutlined />,
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
        <div>
            <IconButton
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
            >
                {menuItems.map((item, index) => (
                    <MenuItem
                        component="a"
                        href={item.link.toString()}
                        target="_blank"
                        rel="noopener noreferrer"
                        key={index}
                        onClick={handleMenuClose}
                    >
                        {item.icon}
                        {item.text}
                    </MenuItem>
                ))}
                <MenuItem
                    component="a"
                    onClick={() => {
                        handleMenuClose();
                        setOpenAboutDialog(true);
                    }}
                >
                    <InfoOutlined />
                    {t("about.title")}
                </MenuItem>
            </Menu>
            <AboutDialog
                open={openAboutDialog}
                closeDialog={() => setOpenAboutDialog(false)}
            />
        </div>
    );
}
