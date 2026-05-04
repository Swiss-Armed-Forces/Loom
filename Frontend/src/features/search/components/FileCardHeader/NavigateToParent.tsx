import { SubdirectoryArrowLeft } from "@mui/icons-material";
import { IconButton, Tooltip } from "@mui/material";

import { useAppDispatch } from "@app/hooks";
import { openDialog } from "@app/slices/commonSlice";
import { DialogType } from "@features/common/utils/enums";
import { FileDetailTab } from "@features/common/utils/enums";

interface NavigateToParentProps {
    parentId: string;
}

export const NavigateToParent = ({ parentId }: NavigateToParentProps) => {
    const dispatch = useAppDispatch();

    const handleClick = () => {
        dispatch(
            openDialog({
                id: "",
                type: DialogType.FileDetail,
                props: { fileId: parentId, tab: FileDetailTab.Rendered },
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
