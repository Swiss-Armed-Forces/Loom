import { IconButton, Menu, MenuItem } from "@mui/material";
import { useState } from "react";
import MenuIcon from "@mui/icons-material/Menu";
import TranslateOutlinedIcon from "@mui/icons-material/TranslateOutlined";
import QueueOutlinedIcon from "@mui/icons-material/QueueOutlined";
import SearchOutlinedIcon from "@mui/icons-material/Search";
export interface Page {
    route: string;
    icon: React.ReactNode;
}
import {
    ApiOutlined,
    CloudCircleOutlined,
    DataObject,
    Insights,
    MailOutlineOutlined,
    SmartToyOutlined,
    TaskOutlined,
    Whatshot,
    DriveFolderUpload,
} from "@mui/icons-material";
import {
    apiHost,
    elasticVueHost,
    flowerHost,
    grafanaHost,
    translateHost,
    minioHost,
    mongoWebHost,
    ollamafrontendHost,
    prometheusHost,
    rabbitHost,
    roundcubeHost,
    rspamdHost,
    traefikHost,
} from "../urls";

export function BurgerMenu() {
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

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
            icon: <TranslateOutlinedIcon />,
        },
        {
            link: ollamafrontendHost,
            text: "Ollama",
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
            icon: <DriveFolderUpload />,
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
            text: "Elasticsearch",
            icon: <SearchOutlinedIcon />,
        },
        {
            link: mongoWebHost,
            text: "MongoDB",
            icon: <DataObject />,
        },
        {
            link: rspamdHost,
            text: "Rspamd",
            icon: <MailOutlineOutlined />,
        },
        {
            link: prometheusHost,
            text: "Prometheus",
            icon: <Whatshot />,
        },
        {
            link: grafanaHost,
            text: "Grafana",
            icon: <Insights />,
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
            </Menu>
        </div>
    );
}
