import path from "node:path";
import { createRequire } from "node:module";

import react from "@vitejs/plugin-react";
import svgr from "vite-plugin-svgr";
import { defineConfig } from "vitest/config";
import { loadEnv } from "vite";

import { normalizePath } from "vite";
import { viteStaticCopy } from "vite-plugin-static-copy";

/**
 * react-pdf related paths
 * see: https://github.com/wojtekmaj/react-pdf/blob/main/test/vite.config.ts
 */
const require = createRequire(import.meta.url);
const cMapsDir = normalizePath(
    path.join(
        path.dirname(require.resolve("pdfjs-dist/package.json")),
        "cmaps",
    ),
);
const standardFontsDir = normalizePath(
    path.join(
        path.dirname(require.resolve("pdfjs-dist/package.json")),
        "standard_fonts",
    ),
);
const wasmDir = normalizePath(
    path.join(path.dirname(require.resolve("pdfjs-dist/package.json")), "wasm"),
);

// https://vitejs.dev/config/

export default ({ mode }) => {
    process.env = { ...process.env, ...loadEnv(mode, process.cwd()) };
    return defineConfig({
        plugins: [
            react(),
            svgr(),
            viteStaticCopy({
                targets: [
                    { src: cMapsDir, dest: "" },
                    { src: standardFontsDir, dest: "" },
                    { src: wasmDir, dest: "" },
                ],
            }),
        ],
        server: {
            host: "0.0.0.0",
            allowedHosts: true,
            port: 80,
            proxy: {
                "/api": {
                    target: process.env.API_BACKEND_URL,
                    ws: true,
                    changeOrigin: true,
                    rewrite: (path) => path.replace(/^\/api/, ""),
                },
            },
        },
        test: {
            globals: true,
            environment: "jsdom",
            setupFiles: "./src/test/setup.ts",
        },
    });
};
