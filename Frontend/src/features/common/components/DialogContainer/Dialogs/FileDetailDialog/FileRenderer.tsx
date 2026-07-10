import {
    Description,
    Download,
    Email,
    Fullscreen,
    FullscreenExit,
    OpenInBrowser,
} from "@mui/icons-material";
import ImageIcon from "@mui/icons-material/Image";
import { Box, IconButton, Tooltip } from "@mui/material";
import { useEffect, useRef, useState } from "react";

import { ImapInfo, RenderedFile } from "@app/api";
import { roundcubeHost, webApiGetFileRendered } from "@features/common/urls";
import { FileRendererType } from "@features/common/utils/enums";

import { FilePdfRenderer } from "./FilePdfRenderer";

interface FileRendererProps {
    fileId: string;
    renderedFile: RenderedFile;
    imap?: ImapInfo;
}

const MODES = [
    {
        value: FileRendererType.Image,
        icon: <ImageIcon fontSize="small" />,
        label: "Image",
    },
    {
        value: FileRendererType.Browser,
        icon: <OpenInBrowser fontSize="small" />,
        label: "Browser",
    },
    {
        value: FileRendererType.Office,
        icon: <Description fontSize="small" />,
        label: "Office",
    },
    {
        value: FileRendererType.Email,
        icon: <Email fontSize="small" />,
        label: "Email",
    },
];

const toolbarButtonSx = (active: boolean) => ({
    borderRadius: 1,
    p: 0.75,
    color: active ? "primary.main" : "text.secondary",
    bgcolor: active ? "action.selected" : "transparent",
    transition: "transform 0.2s ease, opacity 0.2s ease",
    "&:hover": { transform: "scale(1.1)", opacity: 0.8 },
});

export const FileRenderer = ({
    fileId,
    renderedFile,
    imap,
}: FileRendererProps) => {
    const isAvailable = (value: FileRendererType): boolean => {
        switch (value) {
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

    const [type, setType] = useState<FileRendererType>(
        (MODES.map((m) => m.value).find(isAvailable) as FileRendererType) ??
            FileRendererType.Image,
    );

    const containerRef = useRef<HTMLDivElement>(null);
    const [isFullscreen, setIsFullscreen] = useState(false);

    useEffect(() => {
        const handleChange = () =>
            setIsFullscreen(!!document.fullscreenElement);
        document.addEventListener("fullscreenchange", handleChange);
        return () =>
            document.removeEventListener("fullscreenchange", handleChange);
    }, []);

    const toggleFullscreen = () => {
        if (!document.fullscreenElement) {
            containerRef.current?.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    };

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
                    />
                ) : (
                    <div>Email renderer not available</div>
                );
            default:
                return null;
        }
    };

    const downloadUrl = (() => {
        switch (type) {
            case FileRendererType.Image:
                return renderedFile.imageFileId
                    ? webApiGetFileRendered(fileId, renderedFile.imageFileId)
                    : null;
            case FileRendererType.Browser:
                return renderedFile.browserPdfFileId
                    ? webApiGetFileRendered(
                          fileId,
                          renderedFile.browserPdfFileId,
                      )
                    : null;
            case FileRendererType.Office:
                return renderedFile.officePdfFileId
                    ? webApiGetFileRendered(
                          fileId,
                          renderedFile.officePdfFileId,
                      )
                    : null;
            default:
                return null;
        }
    })();

    return (
        <Box
            ref={containerRef}
            sx={{
                width: "100%",
                height: "100%",
                display: "flex",
                flexDirection: "column",
                bgcolor: "background.paper",
            }}
        >
            <Box
                sx={{
                    px: 1,
                    py: 0.5,
                    borderBottom: 1,
                    borderColor: "divider",
                    display: "flex",
                    alignItems: "center",
                    gap: 0.5,
                }}
            >
                {MODES.map(({ value, icon, label }) => {
                    const disabled = !isAvailable(value);
                    return (
                        <Tooltip key={value} title={label}>
                            <span>
                                <IconButton
                                    size="small"
                                    disabled={disabled}
                                    onClick={() => setType(value)}
                                    sx={toolbarButtonSx(type === value)}
                                >
                                    {icon}
                                </IconButton>
                            </span>
                        </Tooltip>
                    );
                })}
                <Box sx={{ flexGrow: 1 }} />
                <Tooltip title="Download rendered file">
                    <span>
                        <IconButton
                            size="small"
                            component="a"
                            href={downloadUrl ?? undefined}
                            download
                            disabled={!downloadUrl}
                            sx={toolbarButtonSx(false)}
                        >
                            <Download fontSize="small" />
                        </IconButton>
                    </span>
                </Tooltip>
                <Tooltip
                    title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
                >
                    <IconButton
                        size="small"
                        onClick={toggleFullscreen}
                        sx={toolbarButtonSx(isFullscreen)}
                    >
                        {isFullscreen ? (
                            <FullscreenExit fontSize="small" />
                        ) : (
                            <Fullscreen fontSize="small" />
                        )}
                    </IconButton>
                </Tooltip>
            </Box>
            <Box sx={{ flex: 1, overflow: "auto" }}>{renderContent()}</Box>
        </Box>
    );
};
