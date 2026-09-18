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
import { useTranslation } from "react-i18next";

import "pdfjs-dist/web/pdf_viewer.css";

import { Point } from "@features/common/utils/model";

import { ContentRendererRef } from "./contentRendererRef";
import { wheelDeltaInPixels, wheelZoomFactor } from "./previewZoom";

// Assign the worker module to globalThis so pdfjs uses the main-thread
// "fake worker" path. This avoids cross-browser issues with module Worker
// creation (Firefox + Vite dev server) and ensures MSW can intercept all
// fetches in demo mode.
(globalThis as any).pdfjsWorker = pdfjsWorker;

// Milliseconds pdf.js keeps a scale change on a pure CSS transform before it
// re-renders the pages at the new scale. Anything in [0, 1000) enables that
// cheap path; 400 is the viewer's own default.
const ZOOM_DRAWING_DELAY_MS = 400;

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
    const { t } = useTranslation();
    const containerRef = useRef<HTMLDivElement>(null);
    const viewerDivRef = useRef<HTMLDivElement>(null);
    const viewerRef = useRef<any>(null);
    const pdfDocRef = useRef<pdfjs.PDFDocumentProxy | null>(null);
    const linkServiceRef = useRef<any>(null);
    const onPageChangeRef = useRef(onPageChange);
    onPageChangeRef.current = onPageChange;

    const [outline, setOutline] = useState<OutlineItem[] | null>(null);
    const [totalPages, setTotalPages] = useState(0);
    const [loadError, setLoadError] = useState(false);

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

    // Drag the document around with the middle mouse button. The left button
    // stays reserved for selecting text in the page's text layer.
    useEffect(() => {
        const container = containerRef.current;
        if (!container) return;

        let lastPointer: Point | null = null;

        const endDrag = () => {
            if (!lastPointer) return;
            lastPointer = null;
            container.style.cursor = "";
        };

        const handleMouseDown = (event: MouseEvent) => {
            if (event.button !== 1) return;
            lastPointer = { x: event.clientX, y: event.clientY };
            container.style.cursor = "grabbing";
            // Suppresses the browser's middle click autoscroll.
            event.preventDefault();
        };

        const handleMouseMove = (event: MouseEvent) => {
            if (!lastPointer) return;
            // A button released outside of the window delivers no mouseup, so
            // the drag has to end on the first move that reports no button.
            if (event.buttons === 0) {
                endDrag();
                return;
            }
            container.scrollLeft -= event.clientX - lastPointer.x;
            container.scrollTop -= event.clientY - lastPointer.y;
            lastPointer = { x: event.clientX, y: event.clientY };
            event.preventDefault();
        };

        container.addEventListener("mousedown", handleMouseDown);
        // On the document, so a drag keeps working outside of the frame.
        document.addEventListener("mousemove", handleMouseMove);
        document.addEventListener("mouseup", endDrag);
        // Covers alt-tabbing away mid drag, which delivers no mouse event at
        // all.
        window.addEventListener("blur", endDrag);

        return () => {
            container.removeEventListener("mousedown", handleMouseDown);
            document.removeEventListener("mousemove", handleMouseMove);
            document.removeEventListener("mouseup", endDrag);
            window.removeEventListener("blur", endDrag);
        };
    }, []);

    // Ctrl (Cmd on macOS) + wheel zooms towards the cursor. Wired up on its own
    // so that it is in place before - and independently of - the document load.
    useEffect(() => {
        const container = containerRef.current;
        if (!container) return;

        // Wheel deltas too small to move the scale yet, carried over to the
        // next event. pdf.js rounds the new scale to two decimals, so the tiny
        // deltas a trackpad pinch emits would otherwise be swallowed one by one
        // and the pinch would do nothing at all.
        let pendingZoomPixels = 0;

        const handleWheel = (event: WheelEvent) => {
            if (!event.ctrlKey && !event.metaKey) return;
            // Before bailing out, so that the browser never zooms the whole
            // page instead - the viewer only exists once the dynamic import and
            // the document load have finished.
            event.preventDefault();
            // There is nothing to scale before the document is in, and letting
            // the deltas pile up until then would land as one jump.
            const viewer = viewerRef.current;
            if (!viewer?.pdfDocument) return;

            const pixels = wheelDeltaInPixels(
                event.deltaY,
                event.deltaMode,
                container.clientHeight,
            );
            // Reversing direction drops whatever was carried over, so a step
            // that never applied - at a scale bound, say - cannot show up as
            // lag when zooming back the other way.
            if (pixels * pendingZoomPixels < 0) pendingZoomPixels = 0;
            pendingZoomPixels += pixels;

            const previousScale: number = viewer.currentScale;
            /*
             * pdf.js anchors the zoom by scrolling `origin` minus the
             * container's `offsetTop`/`offsetLeft`, which is only the pointer's
             * position inside the container when the container's offset parent
             * sits at the top left of the document - the layout its own viewer
             * has, and the reason it is handed raw client coordinates there.
             * This container is positioned inside a detail panel, so its
             * offsets are zero while it sits hundreds of pixels into the
             * window; passing client coordinates would overshoot by exactly
             * that much on every notch and walk the document away from the
             * cursor. Hence the conversion into the space pdf.js measures in.
             *
             * The offsets come from the viewer's own accessor, not from the
             * element: it caches them until the container resizes, so reading
             * the element directly would leave the two halves of this
             * conversion disagreeing whenever the panel has moved without
             * changing size.
             */
            const [containerTop, containerLeft] = viewer.containerTopLeft;
            const rect = container.getBoundingClientRect();
            // The step is relative, so every document zooms at the same pace
            // regardless of the scale its page size is fitted at. The drawing
            // delay keeps a spinning wheel on cheap CSS transforms instead of
            // cancelling and restarting the canvas render on every tick.
            viewer.updateScale({
                scaleFactor: wheelZoomFactor(pendingZoomPixels),
                origin: [
                    event.clientX - rect.left + containerLeft,
                    event.clientY - rect.top + containerTop,
                ],
                drawingDelay: ZOOM_DRAWING_DELAY_MS,
            });
            if (viewer.currentScale !== previousScale) pendingZoomPixels = 0;
        };

        container.addEventListener("wheel", handleWheel, { passive: false });
        return () => container.removeEventListener("wheel", handleWheel);
    }, []);

    useEffect(() => {
        if (!containerRef.current || !viewerDivRef.current) return;
        if (!renderedFileUrl || renderedFileUrl === "about:blank") return;

        let cancelled = false;
        let loadingTask: pdfjs.PDFDocumentLoadingTask | null = null;
        // The viewer observes and listens on the container, which outlives the
        // document, so its teardown has to be triggered explicitly.
        const viewerAbortController = new AbortController();

        setLoadError(false);

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
                // Honoured by the viewer but absent from its published
                // typings, hence the assertion.
                abortSignal: viewerAbortController.signal,
            } as ConstructorParameters<typeof PDFViewer>[0]);
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
                // Destroying the loading task rejects its promise, so closing
                // the dialog mid load lands here as well - that is not a
                // failure worth reporting.
                if (cancelled) return;
                console.error("Failed to load PDF:", e);
                setLoadError(true);
            }
        };

        init();

        return () => {
            cancelled = true;
            viewerRef.current?.setDocument(null);
            // Releases the viewer's resize observer and scroll listener on the
            // container, which is reused for the next document.
            viewerAbortController.abort();
            // destroy() tears the document down as well; an explicit cleanup()
            // on top of it races the worker teardown. It rejects on an
            // in-flight load, which is exactly the case here.
            loadingTask?.destroy().catch(() => {});
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
                        // Advertises that the document can be dragged around,
                        // the same way the image preview does.
                        cursor: "grab",
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
                {loadError && (
                    <Typography
                        variant="body2"
                        sx={{
                            position: "absolute",
                            inset: 0,
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            color: "text.secondary",
                        }}
                    >
                        {t("error.pdfLoadFailed")}
                    </Typography>
                )}
            </Box>
        </Box>
    );
});
