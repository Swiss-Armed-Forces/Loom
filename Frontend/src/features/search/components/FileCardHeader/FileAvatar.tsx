import { Avatar, Badge } from "@mui/material";

import {
    getColorFromString,
    getFontColorFromBackGroundColor,
    getMimeTypeGroupIcon,
} from "@features/common/utils/helpers";

import styles from "./FileAvatar.module.css";

interface FileAvatarProps {
    mimeType: string | null | undefined;
    mimeTypeGroup: string | null | undefined;
    performSearch: (negate: boolean, accumulate: boolean) => void;
    hasBadge: boolean;
}

export const FileAvatar = ({
    mimeType,
    mimeTypeGroup,
    performSearch,
    hasBadge,
}: FileAvatarProps) => {
    const backgroundColor = getColorFromString(mimeType ?? "");
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
                onClick={(e) => performSearch(e.shiftKey, e.ctrlKey)}
                sx={{ backgroundColor, color, width: 36, height: 36 }}
            >
                {getMimeTypeGroupIcon(mimeTypeGroup)}
            </Avatar>
        </Badge>
    );
};
