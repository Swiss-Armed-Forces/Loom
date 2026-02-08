import Avatar from "@mui/material/Avatar";
import styles from "./FileAvatar.module.css";
import {
    getColorFromString,
    getFontColorFromBackGroundColor,
} from "../../common/getColorFromString";

interface FileAvatarProps {
    fileExtension: string;
    performSearch: (query: string) => void;
}

export function FileAvatar({ fileExtension, performSearch }: FileAvatarProps) {
    const backgroundColor = getColorFromString(fileExtension);
    const color = getFontColorFromBackGroundColor(backgroundColor);
    return (
        <Avatar
            className={styles.fileAvatar}
            onClick={() => performSearch(`*.${fileExtension}`)}
            sx={{ backgroundColor, color }}
        >
            {fileExtension}
        </Avatar>
    );
}
