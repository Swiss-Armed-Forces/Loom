import { Fab, Fade } from "@mui/material";
import { ArrowUpward } from "@mui/icons-material";
import { FC } from "react";
import styles from "./ScrollToTop.module.css";

interface ScrollToTopProps {
    visible: boolean;
    onClick: () => void;
}

export const ScrollToTop: FC<ScrollToTopProps> = ({ visible, onClick }) => {
    return (
        <div className={styles.scrollToTopFab}>
            <Fade in={visible}>
                <Fab color="secondary" onClick={onClick}>
                    <ArrowUpward />
                </Fab>
            </Fade>
        </div>
    );
};
