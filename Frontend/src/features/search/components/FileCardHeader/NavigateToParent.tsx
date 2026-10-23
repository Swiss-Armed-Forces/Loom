import { SubdirectoryArrowLeft } from "@mui/icons-material";
import { IconButton } from "@mui/material";
import { memo } from "react";
import React from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch } from "@app/hooks";
import { openFileTabThunk } from "@app/slices/searchSlice";
import { LazyTooltip } from "@features/common/components";

interface NavigateToParentProps {
    parentId: string;
}

export const NavigateToParent = memo(({ parentId }: NavigateToParentProps) => {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();

    const handleClick = (e: React.MouseEvent) => {
        dispatch(openFileTabThunk({ fileId: parentId, background: e.ctrlKey }));
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
