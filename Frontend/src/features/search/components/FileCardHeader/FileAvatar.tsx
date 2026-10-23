import { Avatar, Badge } from "@mui/material";

import {
    getColorFromString,
    getFontColorFromBackGroundColor,
    getMimeTypeGroupIcon,
} from "@features/common/utils/helpers";

import styles from "./FileAvatar.module.css";

/** Edge length of the avatar, in pixels, when no size is asked for. */
const DEFAULT_SIZE_PX = 36;

/** Fraction of the avatar the glyph inside it takes up.
 *
 *  The icon is an SvgIcon carrying its own 24px default, which overflows any
 *  avatar smaller than that and is then clipped by the module's
 *  `overflow: hidden`. Sizing it from the avatar holds the proportion at every
 *  size, from a card header down to a tree row. */
const ICON_SCALE = 0.62;

interface FileAvatarProps {
    mimeType: string | null | undefined;
    mimeTypeGroup: string | null | undefined;
    /** Left out where the avatar is a type indicator rather than a control, as
     *  in a folder-tree row whose own click already does something. */
    performSearch?: (negate: boolean, accumulate: boolean) => void;
    /** `true`/`false` show or hide the unseen dot; leaving it out drops the
     *  badge wrapper altogether. An invisible badge is still an inline-flex box
     *  of its own, which pushes the baseline around in a dense tree row, while
     *  a card always renders one. */
    hasBadge?: boolean;
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
    const avatar = (
        <Avatar
            className={
                performSearch
                    ? `${styles.fileAvatar} ${styles.clickable}`
                    : styles.fileAvatar
            }
            onClick={
                performSearch
                    ? (e) => performSearch(e.shiftKey, e.ctrlKey)
                    : undefined
            }
            sx={{
                backgroundColor,
                color,
                width: size,
                height: size,
                fontSize: size <= 28 ? "0.9rem" : undefined,
                "& .MuiSvgIcon-root": { fontSize: size * ICON_SCALE },
            }}
        >
            {getMimeTypeGroupIcon(mimeTypeGroup)}
        </Avatar>
    );
    if (hasBadge === undefined) return avatar;
    return (
        <Badge
            color="primary"
            variant="dot"
            overlap="circular"
            invisible={!hasBadge}
        >
            {avatar}
        </Badge>
    );
};
