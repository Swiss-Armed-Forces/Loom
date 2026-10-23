import { useAppSelector } from "@app/hooks";
import { selectFieldLayout } from "@app/slices/searchSlice";

import styles from "./ResultCardSkeleton.module.css";

/** Avatar edge length, matching the one the loaded header asks for. */
const AVATAR_PX = 24;

/** Lines of metadata under the header. */
const FIELD_LINES = 1;

/**
 * A result card that has not arrived yet.
 *
 * Shaped like the card it stands in for rather than at one fixed size: a
 * skeleton taller than the row it is replaced by makes the list jump as
 * results land, and three full-height placeholder lines in a one-line layout
 * are a different list from the one that follows.
 *
 * Built from plain elements and a stylesheet rather than from MUI's `Skeleton`
 * and `Box`. This is what a row mounts as while the list is being scrolled
 * quickly - the preview has not arrived yet - so it is on the hot path, and
 * four boxes do not need a styling engine run per card.
 */
export const ResultCardSkeleton = () => {
    const fieldLayout = useAppSelector(selectFieldLayout);
    const lines = fieldLayout === "line" ? 1 : FIELD_LINES;
    const avatar = AVATAR_PX;

    return (
        <div className={styles.skeleton}>
            <div className={styles.header}>
                <div
                    className={styles.avatar}
                    style={{ width: avatar, height: avatar }}
                />
                <div className={`${styles.line} ${styles.title}`} />
            </div>
            {Array.from({ length: lines }, (_unused, line) => (
                <div key={line} className={styles.line} />
            ))}
        </div>
    );
};
