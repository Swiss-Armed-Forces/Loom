import { SubdirectoryArrowLeft } from "@mui/icons-material";
import { IconButton } from "@mui/material";
import { memo } from "react";
import React from "react";
import { useTranslation } from "react-i18next";

import { LazyTooltip } from "@features/common/components";
import { useFileNavigation } from "@features/search/context/FileNavigationContext";

interface NavigateToParentProps {
    parentId: string;
}

export const NavigateToParent = memo(({ parentId }: NavigateToParentProps) => {
    const { t } = useTranslation();
    const { navigateToFile } = useFileNavigation();

    const handleClick = (e: React.MouseEvent) => {
        navigateToFile(parentId, { openInTab: e.ctrlKey });
    };

    const label = t("resultCard.navigateToParent");

    return (
        <LazyTooltip title={label}>
            <IconButton size="small" onClick={handleClick} aria-label={label}>
                <SubdirectoryArrowLeft
                    fontSize="small"
                    sx={{ transform: "rotate(90deg)" }}
                />
            </IconButton>
        </LazyTooltip>
    );
});

NavigateToParent.displayName = "NavigateToParent";
