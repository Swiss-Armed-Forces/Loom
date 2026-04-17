import Avatar from "@mui/material/Avatar";
import styles from "./FileAvatar.module.css";
import {
    getColorFromString,
    getFontColorFromBackGroundColor,
} from "../../common/getColorFromString";
import { Description } from "@mui/icons-material";
import { Badge } from "@mui/material";

interface FileAvatarProps {
    fileExtension: string;
    performSearch: (query: string) => void;
    hasBadge: boolean;
}

export function FileAvatar({
    fileExtension,
    performSearch,
    hasBadge,
}: FileAvatarProps) {
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
                onClick={() => performSearch(`${fileExtension}`)}
                sx={{ backgroundColor, color }}
            >
                {fileExtension || <Description />}
            </Avatar>
        </Badge>
    );
}
