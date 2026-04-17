import { FC } from "react";
import { MoreHoriz } from "@mui/icons-material";
import { IconButton } from "@mui/material";
import styles from "./EllipsisButton.module.css";

interface EllipsisButtonProps {
    onClick: () => void;
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
