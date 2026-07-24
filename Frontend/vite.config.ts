import { createRequire } from "node:module";
import { copyFileSync, readFileSync } from "node:fs";
import path from "node:path";

import react from "@vitejs/plugin-react";
import { type ConfigEnv, loadEnv, type Plugin } from "vite";
import { normalizePath } from "vite";
import { viteStaticCopy } from "vite-plugin-static-copy";
import svgr from "vite-plugin-svgr";
import { defineConfig } from "vitest/config";

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

export default ({ mode }: ConfigEnv) => {
    process.env = { ...process.env, ...loadEnv(mode, process.cwd()) };
    const demo = mode === "demo";
    const pagesBase =
        process.env.GITLAB_CI === "true" && process.env.CI_PAGES_URL
            ? `${new URL(process.env.CI_PAGES_URL).pathname.replace(/\/$/, "")}/`
            : "/";
    return defineConfig({
        base: demo ? pagesBase : "/",
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
            ...(demo
                ? [
                      {
                          name: "loom-demo-worker",
                          generateBundle() {
                              this.emitFile({
                                  type: "asset",
                                  fileName: "mockServiceWorker.js",
                                  source: readFileSync(
                                      path.join(
                                          path.dirname(
                                              require.resolve("msw/package.json"),
                                          ),
                                          "lib/mockServiceWorker.js",
                                      ),
                                  ),
                              });
                          },
                          writeBundle(options) {
                              if (!options.dir) return;
                              copyFileSync(
                                  path.join(options.dir, "index.html"),
                                  path.join(options.dir, "404.html"),
                              );
                          },
                      } satisfies Plugin,
                  ]
                : []),
            {
                name: "loom-demo-entry",
                transformIndexHtml: {
                    order: "pre",
                    handler: (html) =>
                        demo
                            ? html.replace("/src/main.tsx", "/src/demo/main.ts")
                            : html,
                },
            },
        ],
        build: {
            outDir: demo ? "dist-demo" : "dist",
        },
        server: {
            host: "0.0.0.0",
            allowedHosts: true,
            port: 80,
            ...(demo || mode === "test"
                ? { fs: { allow: [path.resolve(__dirname, "..")] } }
                : {}),
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
        resolve: {
            alias: {
                ...(demo
                    ? {
                          "@features/common/components/DemoModeIndicator":
                              path.resolve(
                                  __dirname,
                                  "./src/demo/DemoModeIndicator.tsx",
                              ),
                          "@features/common/demoModeUnavailableAction":
                              path.resolve(
                                  __dirname,
                                  "./src/demo/demoModeUnavailableAction.ts",
                              ),
                          "@features/common/urls": path.resolve(
                              __dirname,
                              "./src/demo/urls.ts",
                          ),
                      }
                    : {}),
                "@app": path.resolve(__dirname, "./src/app"),
                "@features": path.resolve(__dirname, "./src/features"),
                "@middleware": path.resolve(__dirname, "./src/middleware"),
            },
        },
    });
};
