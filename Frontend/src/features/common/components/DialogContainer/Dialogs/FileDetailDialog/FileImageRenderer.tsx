import { Box } from "@mui/material";
import { forwardRef, useImperativeHandle, useRef } from "react";

import { ContentRendererRef } from "./contentRendererRef";

interface FileImageRendererProps {
    src: string;
}

export const FileImageRenderer = forwardRef<
    ContentRendererRef,
    FileImageRendererProps
>(function FileImageRenderer({ src }, ref) {
    const imgRef = useRef<HTMLImageElement>(null);
    const zoomRef = useRef(1);
    const rotationRef = useRef(0);

    const applyTransform = () => {
        if (!imgRef.current) return;
        imgRef.current.style.width = `${zoomRef.current * 100}%`;
        imgRef.current.style.transform = rotationRef.current
            ? `rotate(${rotationRef.current}deg)`
            : "";
    };

    useImperativeHandle(ref, () => ({
        zoomIn: () => {
            zoomRef.current = Math.min(zoomRef.current + 0.25, 5);
            applyTransform();
        },
        zoomOut: () => {
            zoomRef.current = Math.max(zoomRef.current - 0.25, 0.25);
            applyTransform();
        },
        zoomReset: () => {
            zoomRef.current = 1;
            rotationRef.current = 0;
            applyTransform();
        },
        rotate: () => {
            rotationRef.current = (rotationRef.current + 90) % 360;
            applyTransform();
        },
    }));

    return (
        <Box sx={{ flex: 1, overflow: "auto", p: 1 }}>
            <img
                ref={imgRef}
                src={src}
                alt="Rendered file"
                style={{ display: "block", width: "100%", maxWidth: "none" }}
            />
        </Box>
    );
});
