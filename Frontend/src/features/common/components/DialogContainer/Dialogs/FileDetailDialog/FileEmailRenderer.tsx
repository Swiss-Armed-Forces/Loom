import { forwardRef, useImperativeHandle } from "react";

import { ContentRendererRef } from "./contentRendererRef";

interface FileEmailRendererProps {
    src: string;
}

export const FileEmailRenderer = forwardRef<
    ContentRendererRef,
    FileEmailRendererProps
>(function FileEmailRenderer({ src }, ref) {
    useImperativeHandle(ref, () => ({
        zoomIn: () => {},
        zoomOut: () => {},
        zoomReset: () => {},
        rotate: () => {},
    }));

    return (
        <iframe
            src={src}
            style={{ width: "100%", height: "100%", border: "none" }}
        />
    );
});
