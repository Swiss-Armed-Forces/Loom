import { FC } from "react";
import { MoreHoriz } from "@mui/icons-material";
import { IconButton } from "@mui/material";
import styles from "./EllipsisButton.module.css";

interface EllipsisButtonProps {
    click: () => void;
    title?: string;
}
export const EllipsisButton: FC<EllipsisButtonProps> = ({ click, title }) => {
    return (
        <IconButton
            className={styles.ellipsisButton}
            size="large"
            title={title}
            onClick={click}
        >
            <MoreHoriz />
        </IconButton>
    );
};
