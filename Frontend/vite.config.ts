import { createRequire } from "node:module";
import { copyFileSync, cpSync, readFileSync } from "node:fs";
import path from "node:path";

import react from "@vitejs/plugin-react";
import { type ConfigEnv, loadEnv, type Plugin } from "vite";
import svgr from "vite-plugin-svgr";
import { defineConfig } from "vitest/config";

const require = createRequire(import.meta.url);

const pdfjsDir = path.dirname(require.resolve("pdfjs-dist/package.json"));
const pdfjsAssetDirs = ["cmaps", "standard_fonts"] as const;

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
            ...(demo
                ? [
                      {
                          name: "loom-demo-worker",
                          configureServer(server) {
                              const workerSrc = readFileSync(
                                  path.join(
                                      path.dirname(
                                          require.resolve("msw/package.json"),
                                      ),
                                      "lib/mockServiceWorker.js",
                                  ),
                              );
                              server.middlewares.use(
                                  "/mockServiceWorker.js",
                                  (_req, res) => {
                                      res.setHeader(
                                          "Content-Type",
                                          "application/javascript",
                                      );
                                      res.end(workerSrc);
                                  },
                              );
                          },
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
                name: "loom-pdfjs-assets",
                configureServer(server) {
                    server.middlewares.use((req, res, next) => {
                        const url = req.url ?? "";
                        for (const dir of pdfjsAssetDirs) {
                            if (url.startsWith(`/${dir}/`)) {
                                try {
                                    res.end(
                                        readFileSync(path.join(pdfjsDir, url)),
                                    );
                                    return;
                                } catch {
                                    break;
                                }
                            }
                        }
                        next();
                    });
                },
                writeBundle(options) {
                    if (!options.dir) return;
                    for (const dir of pdfjsAssetDirs) {
                        cpSync(
                            path.join(pdfjsDir, dir),
                            path.join(options.dir, dir),
                            { recursive: true },
                        );
                    }
                },
            },
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
