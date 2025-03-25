import react from "@vitejs/plugin-react";
import svgr from "vite-plugin-svgr";
import { defineConfig } from "vitest/config";
import { loadEnv } from "vite";

// https://vitejs.dev/config/

export default ({ mode }) => {
    process.env = { ...process.env, ...loadEnv(mode, process.cwd()) };
    return defineConfig({
        plugins: [react(), svgr()],
        server: {
            host: "0.0.0.0",
            port: parseInt(process.env.PORT) || 5173,
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
