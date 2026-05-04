import { Typography } from "@mui/material";
import { ReactNode } from "react";

import styles from "./HighlightContent.module.css";

export interface HighlightContentProps {
    highlight: ReactNode;
}

export const HighlightContent = ({ highlight }: HighlightContentProps) => {
    return (
        <div className={styles.highlightWrapper}>
            <Typography
                className={styles.resultHighlightText}
                variant="body2"
                component="div"
                sx={{
                    color: "text.secondary",
                }}
            >
                {highlight}
            </Typography>
        </div>
    );
};
