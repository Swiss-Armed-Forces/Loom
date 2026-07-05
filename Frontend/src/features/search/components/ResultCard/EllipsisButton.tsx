import { MoreHoriz } from "@mui/icons-material";
import { IconButton } from "@mui/material";
import { FC, MouseEvent } from "react";

import styles from "./EllipsisButton.module.css";

interface EllipsisButtonProps {
    onClick: (e: MouseEvent) => void;
    title?: string;
}
export const EllipsisButton: FC<EllipsisButtonProps> = ({ onClick, title }) => {
    return (
        <IconButton
            className={styles.ellipsisButton}
            size="large"
            title={title}
            onClick={onClick}
        >
            <MoreHoriz />
        </IconButton>
    );
};
