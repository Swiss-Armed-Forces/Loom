import { Description } from "@mui/icons-material";
import { Avatar, Badge } from "@mui/material";

import {
    getColorFromString,
    getFontColorFromBackGroundColor,
} from "@features/common/utils/helpers";

import styles from "./FileAvatar.module.css";

interface FileAvatarProps {
    fileExtension: string;
    performSearch: (negate: boolean) => void;
    hasBadge: boolean;
}

export const FileAvatar = ({
    fileExtension,
    performSearch,
    hasBadge,
}: FileAvatarProps) => {
    const backgroundColor = getColorFromString(fileExtension);
    const color = getFontColorFromBackGroundColor(backgroundColor);
    return (
        <Badge
            color="primary"
            variant="dot"
            overlap="circular"
            invisible={!hasBadge}
        >
            <Avatar
                className={styles.fileAvatar}
                onClick={(e) => performSearch(e.shiftKey)}
                sx={{ backgroundColor, color }}
            >
                {fileExtension || <Description />}
            </Avatar>
        </Badge>
    );
};
