import { Download } from "@mui/icons-material";
import { IconButton } from "@mui/material";

import { webApiGetFile } from "../../../common/urls";

interface DownloadButtonProps {
    fileId: string;
}

export const DownloadButton = ({ fileId }: DownloadButtonProps) => {
    return (
        <IconButton
            component="a"
            href={webApiGetFile(fileId)}
            target="_blank"
            rel="noopener noreferrer"
            title="Download"
            aria-label="download"
        >
            <Download />
        </IconButton>
    );
};
