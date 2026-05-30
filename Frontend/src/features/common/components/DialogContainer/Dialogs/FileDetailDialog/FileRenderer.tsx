import { Description, Email, OpenInBrowser } from "@mui/icons-material";
import ImageIcon from "@mui/icons-material/Image";
import { ToggleButtonGroup, ToggleButton, Box } from "@mui/material";
import { useState } from "react";

import { ImapInfo, RenderedFile } from "@app/api";
import { roundcubeHost, webApiGetFileRendered } from "@features/common/urls";
import { FileRendererType } from "@features/common/utils/enums";

import { FilePdfRenderer } from "./FilePdfRenderer";

interface FileRendererProps {
    fileId: string;
    renderedFile: RenderedFile;
    imap?: ImapInfo;
}

export const FileRenderer = ({
    fileId,
    renderedFile,
    imap,
}: FileRendererProps) => {
    const isAvailable = (type: FileRendererType): boolean => {
        switch (type) {
            case FileRendererType.Image:
                return !!renderedFile.imageFileId;
            case FileRendererType.Browser:
                return !!renderedFile.browserPdfFileId;
            case FileRendererType.Office:
                return !!renderedFile.officePdfFileId;
            case FileRendererType.Email:
                return !!imap;
            default:
                return false;
        }
    };

    // Set to first available renderer type on initialization
    const [type, setType] = useState<FileRendererType>(
        (Object.values(FileRendererType).find(
            isAvailable,
        ) as FileRendererType) ?? FileRendererType.Image,
    );

    const renderContent = () => {
        switch (type) {
            case FileRendererType.Image:
                return renderedFile.imageFileId ? (
                    <img
                        src={webApiGetFileRendered(
                            fileId,
                            renderedFile.imageFileId,
                        )}
                        alt="Rendered file"
                        style={{ width: "100%" }}
                    />
                ) : (
                    <div>Image renderer not available</div>
                );
            case FileRendererType.Browser:
                return renderedFile.browserPdfFileId ? (
                    <FilePdfRenderer
                        renderedFileUrl={webApiGetFileRendered(
                            fileId,
                            renderedFile.browserPdfFileId,
                        )}
                    />
                ) : (
                    <div>Browser renderer not available</div>
                );
            case FileRendererType.Office:
                return renderedFile.officePdfFileId ? (
                    <FilePdfRenderer
                        renderedFileUrl={webApiGetFileRendered(
                            fileId,
                            renderedFile.officePdfFileId,
                        )}
                    />
                ) : (
                    <div>Office renderer not available</div>
                );
            case FileRendererType.Email:
                return imap ? (
                    <iframe
                        src={`${roundcubeHost}?_task=mail&_extwin=1&_action=show&_uid=${imap.uid}&_mbox=${encodeURIComponent(imap.folderUtf7)}`}
                        style={{
                            width: "100%",
                            height: "100%",
                            border: "none",
                        }}
                    ></iframe>
                ) : (
                    <div>Email renderer not available</div>
                );
            default:
                return null;
        }
    };

    const handleChange = (_: unknown, newType: FileRendererType) => {
        if (newType != type) setType(newType);
    };

    return (
        <Box
            sx={{
                width: "100%",
                height: "100%",
                display: "flex",
                flexDirection: "column",
            }}
        >
            <Box sx={{ p: 2, borderBottom: 1, borderColor: "divider" }}>
                <ToggleButtonGroup
                    value={type}
                    exclusive
                    onChange={handleChange}
                    aria-label="file renderer"
                    size="small"
                >
                    <ToggleButton
                        value={FileRendererType.Image}
                        disabled={!renderedFile.imageFileId}
                        aria-label="image"
                    >
                        <ImageIcon sx={{ mr: 1 }} fontSize="small" />
                        Image
                    </ToggleButton>
                    <ToggleButton
                        value={FileRendererType.Browser}
                        disabled={!renderedFile.browserPdfFileId}
                        aria-label="browser"
                    >
                        <OpenInBrowser sx={{ mr: 1 }} fontSize="small" />
                        Browser
                    </ToggleButton>
                    <ToggleButton
                        value={FileRendererType.Office}
                        disabled={!renderedFile.officePdfFileId}
                        aria-label="office"
                    >
                        <Description sx={{ mr: 1 }} fontSize="small" />
                        Office
                    </ToggleButton>
                    <ToggleButton
                        value={FileRendererType.Email}
                        disabled={!imap}
                        aria-label="email"
                    >
                        <Email sx={{ mr: 1 }} fontSize="small" />
                        Email
                    </ToggleButton>
                </ToggleButtonGroup>
            </Box>
            <Box sx={{ flex: 1, overflow: "auto" }}>{renderContent()}</Box>
        </Box>
    );
};
