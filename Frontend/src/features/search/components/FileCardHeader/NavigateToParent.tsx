import { SubdirectoryArrowLeft } from "@mui/icons-material";
import { IconButton, Tooltip } from "@mui/material";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import { openDialog, selectLastFileDetailTab } from "@app/slices/commonSlice";
import { DialogType } from "@features/common/utils/enums";

interface NavigateToParentProps {
    parentId: string;
}

export const NavigateToParent = ({ parentId }: NavigateToParentProps) => {
    const dispatch = useAppDispatch();
    const lastTab = useAppSelector(selectLastFileDetailTab);

    const handleClick = () => {
        dispatch(
            openDialog({
                id: "",
                type: DialogType.FileDetail,
                props: { fileId: parentId, tab: lastTab },
            }),
        );
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
