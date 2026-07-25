import { Box, Typography } from "@mui/material";
import * as pdfjs from "pdfjs-dist";
import * as pdfjsWorker from "pdfjs-dist/build/pdf.worker.min.mjs";
import {
    forwardRef,
    useEffect,
    useImperativeHandle,
    useRef,
    useState,
} from "react";

import "pdfjs-dist/web/pdf_viewer.css";

import { ContentRendererRef } from "./contentRendererRef";

// Assign the worker module to globalThis so pdfjs uses the main-thread
// "fake worker" path. This avoids cross-browser issues with module Worker
// creation (Firefox + Vite dev server) and ensures MSW can intercept all
// fetches in demo mode.
(globalThis as any).pdfjsWorker = pdfjsWorker;

interface OutlineItem {
    title: string;
    dest: any;
    items: OutlineItem[];
}

interface PageThumbnailProps {
    doc: pdfjs.PDFDocumentProxy;
    pageNum: number;
    onClick: () => void;
}

const PageThumbnail = ({ doc, pageNum, onClick }: PageThumbnailProps) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        let rendered = false;
        const observer = new IntersectionObserver(async ([entry]) => {
            if (!entry.isIntersecting || rendered) return;
            rendered = true;
            const page = await doc.getPage(pageNum);
            const viewport = page.getViewport({ scale: 0.15 });
            canvas.width = viewport.width;
            canvas.height = viewport.height;
            await page.render({ canvas, viewport }).promise;
            page.cleanup();
        });
        observer.observe(canvas);
        return () => observer.disconnect();
    }, [doc, pageNum]);

    return (
        <Box
            onClick={onClick}
            sx={{
                cursor: "pointer",
                p: 0.5,
                "&:hover": { bgcolor: "action.hover" },
            }}
        >
            <canvas
                ref={canvasRef}
                style={{ width: "100%", display: "block", background: "white" }}
            />
            <Typography
                variant="caption"
                sx={{
                    display: "block",
                    textAlign: "center",
                    color: "text.secondary",
                    py: 0.25,
                }}
            >
                {pageNum}
            </Typography>
        </Box>
    );
};

interface FilePdfRendererProps {
    renderedFileUrl: string;
    sidebarMode?: "none" | "outline" | "thumbnails";
    onPageChange?: (page: number, total: number) => void;
}

export const FilePdfRenderer = forwardRef<
    ContentRendererRef,
    FilePdfRendererProps
>(function FilePdfRenderer(
    { renderedFileUrl, sidebarMode = "none", onPageChange },
    ref,
) {
    const containerRef = useRef<HTMLDivElement>(null);
    const viewerDivRef = useRef<HTMLDivElement>(null);
    const viewerRef = useRef<any>(null);
    const pdfDocRef = useRef<pdfjs.PDFDocumentProxy | null>(null);
    const linkServiceRef = useRef<any>(null);
    const onPageChangeRef = useRef(onPageChange);
    onPageChangeRef.current = onPageChange;

    const [outline, setOutline] = useState<OutlineItem[] | null>(null);
    const [totalPages, setTotalPages] = useState(0);

    useImperativeHandle(ref, () => ({
        zoomIn: () => viewerRef.current?.increaseScale(),
        zoomOut: () => viewerRef.current?.decreaseScale(),
        zoomReset: () => {
            if (viewerRef.current)
                viewerRef.current.currentScaleValue = "page-width";
        },
        rotate: () => {
            if (viewerRef.current)
                viewerRef.current.pagesRotation =
                    (viewerRef.current.pagesRotation + 90) % 360;
        },
    }));

    useEffect(() => {
        if (!containerRef.current || !viewerDivRef.current) return;
        if (!renderedFileUrl || renderedFileUrl === "about:blank") return;

        let cancelled = false;
        let loadingTask: pdfjs.PDFDocumentLoadingTask | null = null;

        const init = async () => {
            const { EventBus, PDFLinkService, PDFViewer } =
                await import("pdfjs-dist/web/pdf_viewer.mjs");

            if (cancelled) return;

            const eventBus = new EventBus();
            const linkService = new PDFLinkService({ eventBus });

            const viewer = new PDFViewer({
                container: containerRef.current!,
                viewer: viewerDivRef.current!,
                eventBus,
                linkService,
                removePageBorders: true,
            });
            viewerRef.current = viewer;
            linkServiceRef.current = linkService;
            linkService.setViewer(viewer);

            eventBus.on("pagesinit", () => {
                viewer.currentScaleValue = "page-width";
            });

            eventBus.on(
                "pagechanging",
                ({ pageNumber }: { pageNumber: number }) => {
                    onPageChangeRef.current?.(
                        pageNumber,
                        pdfDocRef.current?.numPages ?? 0,
                    );
                },
            );

            loadingTask = pdfjs.getDocument({
                url: renderedFileUrl,
                cMapUrl: `${import.meta.env.BASE_URL}cmaps/`,
                cMapPacked: true,
                standardFontDataUrl: `${import.meta.env.BASE_URL}standard_fonts/`,
            });

            try {
                const pdfDocument = await loadingTask.promise;
                if (cancelled) {
                    await pdfDocument.cleanup();
                    return;
                }
                pdfDocRef.current = pdfDocument;
                viewer.setDocument(pdfDocument);
                linkService.setDocument(pdfDocument);

                setTotalPages(pdfDocument.numPages);
                onPageChangeRef.current?.(1, pdfDocument.numPages);

                const fetchedOutline = await pdfDocument.getOutline();
                if (!cancelled) setOutline(fetchedOutline ?? []);
            } catch (e) {
                console.error("Failed to load PDF:", e);
            }
        };

        init();

        return () => {
            cancelled = true;
            const doc = pdfDocRef.current;
            loadingTask?.destroy();
            doc?.cleanup();
            pdfDocRef.current = null;
            viewerRef.current = null;
            linkServiceRef.current = null;
            setOutline(null);
            setTotalPages(0);
        };
    }, [renderedFileUrl]);

    const navigateToOutlineItem = async (dest: any) => {
        const linkService = linkServiceRef.current;
        if (!linkService) return;
        await linkService.goToDestination(dest);
    };

    const navigateToPage = (pageNum: number) => {
        if (viewerRef.current) viewerRef.current.currentPageNumber = pageNum;
    };

    const renderOutlineItems = (items: OutlineItem[], depth = 0) =>
        items.map((item, i) => (
            <Box key={i}>
                <Box
                    component="button"
                    onClick={() =>
                        item.dest && navigateToOutlineItem(item.dest)
                    }
                    sx={{
                        display: "block",
                        width: "100%",
                        textAlign: "left",
                        background: "none",
                        border: "none",
                        cursor: item.dest ? "pointer" : "default",
                        pl: 1 + depth * 1.5,
                        pr: 1,
                        py: 0.5,
                        fontSize: 13,
                        color: "text.primary",
                        "&:hover": item.dest
                            ? { bgcolor: "action.hover" }
                            : undefined,
                    }}
                >
                    {item.title}
                </Box>
                {item.items?.length > 0 &&
                    renderOutlineItems(item.items, depth + 1)}
            </Box>
        ));

    const showSidebar = sidebarMode !== "none";

    return (
        <Box
            sx={{
                flex: 1,
                display: "flex",
                overflow: "hidden",
                bgcolor: "grey.400",
            }}
        >
            {showSidebar && (
                <Box
                    sx={{
                        width: 220,
                        flexShrink: 0,
                        bgcolor: "background.paper",
                        borderRight: 1,
                        borderColor: "divider",
                        overflow: "auto",
                    }}
                >
                    {sidebarMode === "outline" && (
                        <Box>
                            {outline === null && (
                                <Typography
                                    variant="caption"
                                    sx={{
                                        p: 1,
                                        display: "block",
                                        color: "text.secondary",
                                    }}
                                >
                                    Loading…
                                </Typography>
                            )}
                            {outline !== null && outline.length === 0 && (
                                <Typography
                                    variant="caption"
                                    sx={{
                                        p: 1,
                                        display: "block",
                                        color: "text.secondary",
                                    }}
                                >
                                    No outline available
                                </Typography>
                            )}
                            {outline !== null &&
                                outline.length > 0 &&
                                renderOutlineItems(outline)}
                        </Box>
                    )}
                    {sidebarMode === "thumbnails" &&
                        pdfDocRef.current !== null && (
                            <Box>
                                {Array.from(
                                    { length: totalPages },
                                    (_, i) => i + 1,
                                ).map((pageNum) => (
                                    <PageThumbnail
                                        key={pageNum}
                                        doc={pdfDocRef.current!}
                                        pageNum={pageNum}
                                        onClick={() => navigateToPage(pageNum)}
                                    />
                                ))}
                            </Box>
                        )}
                </Box>
            )}
            <Box sx={{ flex: 1, position: "relative" }}>
                <Box
                    ref={containerRef}
                    sx={{
                        position: "absolute",
                        inset: 0,
                        overflow: "auto",
                        // Give each page a drop shadow so boundaries are visible
                        // against the background regardless of theme.
                        "& .pdfViewer .page": {
                            boxShadow:
                                "0 2px 8px rgba(0,0,0,0.35), 0 0 0 1px rgba(0,0,0,0.08)",
                        },
                    }}
                >
                    <div ref={viewerDivRef} className="pdfViewer" />
                </Box>
            </Box>
        </Box>
    );
});
