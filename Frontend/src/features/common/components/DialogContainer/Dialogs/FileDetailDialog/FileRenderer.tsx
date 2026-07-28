import {
    Description,
    Download,
    Email,
    FitScreen,
    FormatListBulleted,
    Fullscreen,
    FullscreenExit,
    GridView,
    OpenInBrowser,
    RotateRight,
    ZoomIn,
    ZoomOut,
} from "@mui/icons-material";
import ImageIcon from "@mui/icons-material/Image";
import { Box, IconButton, Tooltip, Typography } from "@mui/material";
import { useEffect, useRef, useState } from "react";

import { ImapInfo, RenderedFile } from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    selectPendingFullscreenFileId,
    setPendingFullscreenFileId,
} from "@app/slices/searchSlice";
import { roundcubeHost, webApiGetFileRendered } from "@features/common/urls";
import { FileRendererType } from "@features/common/utils/enums";

import { ContentRendererRef } from "./contentRendererRef";
import { FileEmailRenderer } from "./FileEmailRenderer";
import { FileImageRenderer } from "./FileImageRenderer";
import { FilePdfRenderer } from "./FilePdfRenderer";

interface FileRendererProps {
    fileId: string;
    renderedFile: RenderedFile;
    imap?: ImapInfo;
}

const MODES = [
    {
        value: FileRendererType.Office,
        icon: <Description fontSize="small" />,
        label: "Office",
    },
    {
        value: FileRendererType.Browser,
        icon: <OpenInBrowser fontSize="small" />,
        label: "Browser",
    },
    {
        value: FileRendererType.Image,
        icon: <ImageIcon fontSize="small" />,
        label: "Image",
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
    const dispatch = useAppDispatch();
    const isThisFilePending = useAppSelector(
        (state) => selectPendingFullscreenFileId(state) === fileId,
    );
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

    const canZoomRotate = type !== FileRendererType.Email;
    const isPdfRenderer =
        type === FileRendererType.Browser || type === FileRendererType.Office;

    const rendererRef = useRef<ContentRendererRef>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [sidebarMode, setSidebarMode] = useState<
        "none" | "outline" | "thumbnails"
    >("none");
    const [pageInfo, setPageInfo] = useState<{
        current: number;
        total: number;
    } | null>(null);

    useEffect(() => {
        if (!isPdfRenderer) {
            setSidebarMode("none");
            setPageInfo(null);
        }
    }, [isPdfRenderer]);

    const toggleOutline = () =>
        setSidebarMode((prev) => (prev === "outline" ? "none" : "outline"));
    const toggleThumbnails = () =>
        setSidebarMode((prev) =>
            prev === "thumbnails" ? "none" : "thumbnails",
        );

    useEffect(() => {
        const handleChange = () =>
            setIsFullscreen(!!document.fullscreenElement);
        document.addEventListener("fullscreenchange", handleChange);
        return () =>
            document.removeEventListener("fullscreenchange", handleChange);
    }, []);

    // When the keyboard shortcut opens this tab from the card view, a pending
    // fullscreen request is stored in Redux. Consume it on mount while
    // transient user activation (~5s from the keypress) is still valid.
    useEffect(() => {
        if (isThisFilePending) {
            dispatch(setPendingFullscreenFileId(null));
            containerRef.current?.requestFullscreen().catch((err) => {
                console.error("requestFullscreen failed:", err);
            });
        }
    }, [isThisFilePending, dispatch]);

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
                    <FileImageRenderer
                        ref={rendererRef}
                        src={webApiGetFileRendered(
                            fileId,
                            renderedFile.imageFileId,
                        )}
                    />
                ) : (
                    <div>Image renderer not available</div>
                );
            case FileRendererType.Browser:
                return renderedFile.browserPdfFileId ? (
                    <FilePdfRenderer
                        ref={rendererRef}
                        renderedFileUrl={webApiGetFileRendered(
                            fileId,
                            renderedFile.browserPdfFileId,
                        )}
                        sidebarMode={sidebarMode}
                        onPageChange={(current, total) =>
                            setPageInfo({ current, total })
                        }
                    />
                ) : (
                    <div>Browser renderer not available</div>
                );
            case FileRendererType.Office:
                return renderedFile.officePdfFileId ? (
                    <FilePdfRenderer
                        ref={rendererRef}
                        renderedFileUrl={webApiGetFileRendered(
                            fileId,
                            renderedFile.officePdfFileId,
                        )}
                        sidebarMode={sidebarMode}
                        onPageChange={(current, total) =>
                            setPageInfo({ current, total })
                        }
                    />
                ) : (
                    <div>Office renderer not available</div>
                );
            case FileRendererType.Email:
                return imap ? (
                    <FileEmailRenderer
                        ref={rendererRef}
                        src={`${roundcubeHost}?_task=mail&_extwin=1&_action=show&_uid=${imap.uid}&_mbox=${encodeURIComponent(imap.folderUtf7)}`}
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
                {/* Left: renderer mode buttons */}
                <Box sx={{ flex: 1, display: "flex", gap: 0.5 }}>
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
                </Box>

                {/* Center-left: PDF sidebar toggles + page info */}
                <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                    <Tooltip title="Toggle outline">
                        <span>
                            <IconButton
                                size="small"
                                disabled={!isPdfRenderer}
                                onClick={toggleOutline}
                                sx={toolbarButtonSx(sidebarMode === "outline")}
                            >
                                <FormatListBulleted fontSize="small" />
                            </IconButton>
                        </span>
                    </Tooltip>
                    <Tooltip title="Toggle thumbnails">
                        <span>
                            <IconButton
                                size="small"
                                disabled={!isPdfRenderer}
                                onClick={toggleThumbnails}
                                sx={toolbarButtonSx(
                                    sidebarMode === "thumbnails",
                                )}
                            >
                                <GridView fontSize="small" />
                            </IconButton>
                        </span>
                    </Tooltip>
                    {pageInfo && (
                        <Typography
                            variant="caption"
                            sx={{
                                color: "text.secondary",
                                minWidth: 50,
                                textAlign: "center",
                            }}
                        >
                            {pageInfo.current} / {pageInfo.total}
                        </Typography>
                    )}
                </Box>

                {/* Center: zoom controls */}
                <Box sx={{ display: "flex", gap: 0.5 }}>
                    <Tooltip title="Zoom out">
                        <span>
                            <IconButton
                                size="small"
                                disabled={!canZoomRotate}
                                onClick={() => rendererRef.current?.zoomOut()}
                                sx={toolbarButtonSx(false)}
                            >
                                <ZoomOut fontSize="small" />
                            </IconButton>
                        </span>
                    </Tooltip>
                    <Tooltip title="Fit to width">
                        <span>
                            <IconButton
                                size="small"
                                disabled={!canZoomRotate}
                                onClick={() => rendererRef.current?.zoomReset()}
                                sx={toolbarButtonSx(false)}
                            >
                                <FitScreen fontSize="small" />
                            </IconButton>
                        </span>
                    </Tooltip>
                    <Tooltip title="Zoom in">
                        <span>
                            <IconButton
                                size="small"
                                disabled={!canZoomRotate}
                                onClick={() => rendererRef.current?.zoomIn()}
                                sx={toolbarButtonSx(false)}
                            >
                                <ZoomIn fontSize="small" />
                            </IconButton>
                        </span>
                    </Tooltip>
                    <Tooltip title="Rotate 90°">
                        <span>
                            <IconButton
                                size="small"
                                disabled={!canZoomRotate}
                                onClick={() => rendererRef.current?.rotate()}
                                sx={toolbarButtonSx(false)}
                            >
                                <RotateRight fontSize="small" />
                            </IconButton>
                        </span>
                    </Tooltip>
                </Box>

                {/* Right: download + fullscreen */}
                <Box
                    sx={{
                        flex: 1,
                        display: "flex",
                        gap: 0.5,
                        justifyContent: "flex-end",
                    }}
                >
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
                            aria-label="fullscreen"
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
            </Box>
            <Box
                sx={{
                    flex: 1,
                    overflow: "auto",
                    display: "flex",
                    flexDirection: "column",
                }}
            >
                {renderContent()}
            </Box>
        </Box>
    );
};
