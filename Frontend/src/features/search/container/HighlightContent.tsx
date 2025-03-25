import { Typography } from "@mui/material";
import styles from "./HighlightContent.module.css";
import { FC, ReactNode } from "react";

export interface HighlightContentProps {
    highlight: ReactNode;
}

export const HighlightContent: FC<HighlightContentProps> = ({ highlight }) => {
    return (
        <div className={styles.highlightWrapper}>
            <Typography
                className={styles.resultHighlightText}
                variant="body2"
                component="div"
                color="text.secondary"
            >
                {highlight}
            </Typography>
        </div>
    );
};
