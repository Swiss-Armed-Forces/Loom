import { Download } from "@mui/icons-material";
import { IconButton } from "@mui/material";
import { webApiGetFile } from "../urls";

interface DownloadButtonProps {
    fileId: string;
}

export function DownloadButton({ fileId }: DownloadButtonProps) {
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
}
