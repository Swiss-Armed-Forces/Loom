import { SubdirectoryArrowLeft } from "@mui/icons-material";
import { IconButton, Tooltip } from "@mui/material";
import React from "react";

import { useAppDispatch } from "@app/hooks";
import { openFileTabThunk } from "@app/slices/searchSlice";

interface NavigateToParentProps {
    parentId: string;
}

export const NavigateToParent = ({ parentId }: NavigateToParentProps) => {
    const dispatch = useAppDispatch();

    const handleClick = (e: React.MouseEvent) => {
        dispatch(openFileTabThunk({ fileId: parentId, background: e.ctrlKey }));
    };

    return (
        <Tooltip title="Navigate to parent">
            <IconButton
                size="small"
                onClick={handleClick}
                aria-label="Navigate to parent"
            >
                <SubdirectoryArrowLeft
                    fontSize="small"
                    sx={{ transform: "rotate(90deg)" }}
                />
            </IconButton>
        </Tooltip>
    );
};
