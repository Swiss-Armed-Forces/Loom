import { Dispatch, SetStateAction, useRef, useState } from "react";

export interface UseFileUploadResult {
    files: File[];
    setFiles: Dispatch<SetStateAction<File[]>>;
    isLoading: boolean;
    overallProgress: number | undefined;
    handleUpload: (
        uploadFn: (
            file: File,
            onProgress: (percent: number) => void,
            signal: AbortSignal,
        ) => Promise<void>,
    ) => Promise<void>;
    abortUpload: () => void;
}

export const useFileUpload = (): UseFileUploadResult => {
    const [files, setFiles] = useState<File[]>([]);
    const [fileProgress, setFileProgress] = useState<Map<File, number>>(
        new Map(),
    );
    const [isLoading, setIsLoading] = useState(false);
    const abortControllerRef = useRef<AbortController | null>(null);

    const overallProgress: number | undefined = isLoading
        ? fileProgress.size > 0
            ? Math.round(
                  Array.from(fileProgress.values()).reduce(
                      (sum, p) => sum + p,
                      0,
                  ) / fileProgress.size,
              )
            : 0
        : undefined;

    const handleUpload = async (
        uploadFn: (
            file: File,
            onProgress: (percent: number) => void,
            signal: AbortSignal,
        ) => Promise<void>,
    ): Promise<void> => {
        const controller = new AbortController();
        abortControllerRef.current = controller;

        setIsLoading(true);
        setFileProgress(new Map(files.map((f) => [f, 0])));
        try {
            await Promise.all(
                files.map((file) =>
                    uploadFn(
                        file,
                        (percent) => {
                            setFileProgress((prev) =>
                                new Map(prev).set(file, percent),
                            );
                        },
                        controller.signal,
                    ),
                ),
            );
        } finally {
            abortControllerRef.current = null;
            setIsLoading(false);
            setFileProgress(new Map());
        }
    };

    const abortUpload = () => {
        abortControllerRef.current?.abort();
    };

    return {
        files,
        setFiles,
        isLoading,
        overallProgress,
        handleUpload,
        abortUpload,
    };
};
