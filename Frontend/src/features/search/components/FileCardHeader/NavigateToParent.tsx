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
                sx={{
                    transform: "rotate(90deg)",
                    cursor: "pointer",
                    "&:hover": {
                        backgroundColor: "action.hover",
                        transform: "rotate(90deg) scale(1.1)",
                    },
                    transition: "all 0.2s ease-in-out",
                }}
                aria-label="Navigate to parent"
            >
                <SubdirectoryArrowLeft fontSize="small" />
            </IconButton>
        </Tooltip>
    );
};
