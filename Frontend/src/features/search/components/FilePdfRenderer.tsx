import { useState, useRef, useEffect } from "react";
import { pdfjs, Document, Page } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import { DocumentCallback } from "react-pdf/dist/shared/types.js";

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
    "pdfjs-dist/build/pdf.worker.min.mjs",
    import.meta.url,
).toString();

const options = {
    cMapUrl: "/cmaps/",
    standardFontDataUrl: "/standard_fonts/",
    wasmUrl: "/wasm/",
};

interface FilePdfRendererProps {
    renderedFileUrl: string;
}

export function FilePdfRenderer({ renderedFileUrl }: FilePdfRendererProps) {
    const [pdfNumPages, setPdfNumPages] = useState<number>();
    const [containerWidth, setContainerWidth] = useState<number>();
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const updateWidth = () => {
            if (containerRef.current) {
                setContainerWidth(containerRef.current.offsetWidth);
            }
        };

        updateWidth();
        window.addEventListener("resize", updateWidth);
        return () => window.removeEventListener("resize", updateWidth);
    }, []);

    function onPdfDocumentLoadSuccess({
        numPages: nextNumPages,
    }: DocumentCallback): void {
        setPdfNumPages(nextNumPages);
    }

    return (
        <div ref={containerRef} style={{ width: "100%" }}>
            <Document
                file={renderedFileUrl}
                onLoadSuccess={onPdfDocumentLoadSuccess}
                options={options}
            >
                {Array.from(new Array(pdfNumPages), (_el, index) => (
                    <Page
                        key={`page_${index + 1}`}
                        pageNumber={index + 1}
                        width={containerWidth}
                    />
                ))}
            </Document>
        </div>
    );
}
