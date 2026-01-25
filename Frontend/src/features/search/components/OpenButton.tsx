import { OpenInNewOutlined } from "@mui/icons-material";
import { IconButton } from "@mui/material";
import { webApiGetFileOpen } from "../../common/urls";

interface OpenProps {
    file_id: string;
    disabled?: boolean;
}

export function OpenButton({ file_id, disabled = false }: OpenProps) {
    return (
        <IconButton
            disabled={disabled}
            component="a"
            href={webApiGetFileOpen(file_id)}
            target="_blank"
            rel="noopener noreferrer"
            title="Open"
            aria-label="open"
        >
            <OpenInNewOutlined />
        </IconButton>
    );
}
