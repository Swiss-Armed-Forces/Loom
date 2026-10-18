import { Avatar, Badge } from "@mui/material";

import {
    getColorFromString,
    getFontColorFromBackGroundColor,
    getMimeTypeGroupIcon,
} from "@features/common/utils/helpers";

import styles from "./FileAvatar.module.css";

/** Edge length of the avatar, in pixels, when no size is asked for. */
const DEFAULT_SIZE_PX = 36;

interface FileAvatarProps {
    mimeType: string | null | undefined;
    mimeTypeGroup: string | null | undefined;
    performSearch: (negate: boolean, accumulate: boolean) => void;
    hasBadge: boolean;
    /** Edge length in pixels. The avatar is the tallest thing in a card
     *  header, so a dense card asks for a smaller one. */
    size?: number;
}

export const FileAvatar = ({
    mimeType,
    mimeTypeGroup,
    performSearch,
    hasBadge,
    size = DEFAULT_SIZE_PX,
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
                sx={{
                    backgroundColor,
                    color,
                    width: size,
                    height: size,
                    fontSize: size <= 28 ? "0.9rem" : undefined,
                }}
            >
                {getMimeTypeGroupIcon(mimeTypeGroup)}
            </Avatar>
        </Badge>
    );
};
