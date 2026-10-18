import { Box, Skeleton } from "@mui/material";

import { useAppSelector } from "@app/hooks";
import {
    NamedDensity,
    selectFieldLayout,
    selectResolvedCardDensity,
} from "@app/slices/searchSlice";

/** Avatar edge length, matching the one the loaded header asks for. */
const AVATAR_PX: Record<NamedDensity, number> = {
    compact: 24,
    standard: 36,
    full: 50,
};

/** Lines of metadata under the header, as many as the density shows. */
const FIELD_LINES: Record<NamedDensity, number> = {
    compact: 1,
    standard: 2,
    full: 3,
};

/**
 * A result card that has not arrived yet.
 *
 * Shaped like the card it stands in for rather than at one fixed size: a
 * skeleton taller than the row it is replaced by makes the list jump as
 * results land, and three full-height placeholder lines in a one-line layout
 * are a different list from the one that follows.
 */
export const ResultCardSkeleton = () => {
    const density = useAppSelector(selectResolvedCardDensity);
    const fieldLayout = useAppSelector(selectFieldLayout);
    // One line is all the line layout ever draws, whatever the spacing.
    const lines = fieldLayout === "line" ? 1 : FIELD_LINES[density];
    const avatar = AVATAR_PX[density];

    return (
        <Box
            sx={{
                py: "var(--loom-card-padding, 0.5rem)",
                px: { xs: 1, sm: 2 },
            }}
        >
            <Box
                sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: "var(--loom-row-gap, 0.5rem)",
                    mb: "var(--loom-card-padding, 0.5rem)",
                }}
            >
                <Skeleton variant="circular" width={avatar} height={avatar} />
                <Skeleton variant="text" sx={{ flexGrow: 1 }} />
            </Box>
            {Array.from({ length: lines }, (_, line) => (
                <Skeleton
                    key={line}
                    variant="text"
                    sx={{ lineHeight: "var(--loom-row-line-height, 1.4)" }}
                />
            ))}
        </Box>
    );
};
