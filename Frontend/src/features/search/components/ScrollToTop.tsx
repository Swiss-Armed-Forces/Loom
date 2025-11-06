import { Fab, Fade } from "@mui/material";
import { ArrowUpward } from "@mui/icons-material";
import { FC } from "react";
import styles from "./ScrollToTop.module.css";
import React from "react";

interface ScrollToTopProps {
    visible: boolean;
    onClick: () => void;
}

export const ScrollToTop: FC<ScrollToTopProps> = React.memo(
    ({ visible, onClick }: ScrollToTopProps) => {
        return (
            <div className={styles.scrollToTopFab}>
                <Fade in={visible}>
                    <Fab color="secondary" onClick={onClick}>
                        <ArrowUpward />
                    </Fab>
                </Fade>
            </div>
        );
    },
);

ScrollToTop.displayName = "ScrollToTop";
