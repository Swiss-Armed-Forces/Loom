/// <reference types="vite/client" />
/// <reference types="vite-plugin-svgr/client" />

declare module "pdfjs-dist/build/pdf.worker.min.mjs";

interface Map<K, V> {
    getOrInsertComputed(key: K, callbackFn: (key: K) => V): V;
}

interface Uint8Array {
    toHex(): string;
}
