import { defineConfig, globalIgnores } from "eslint/config";
import js from "@eslint/js";
import globals from "globals";

import tsParser from "@typescript-eslint/parser";
import tseslint from "typescript-eslint";

import reactPlugin from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";

import reactRefresh from "eslint-plugin-react-refresh";
import unusedImports from "eslint-plugin-unused-imports";

import prettierRecommended from "eslint-plugin-prettier/recommended";

export default defineConfig([
    // Ignore generated artifacts and non-source files we don't want to lint.
    globalIgnores(["dist/", "**/THIRD-PARTY.md"]),

    // Baseline ESLint rules for common correctness issues in JS.
    js.configs.recommended,

    // TypeScript ruleset (flat-config native). Provides the recommended @typescript-eslint rules.
    // This is layered on top of the JS baseline.
    ...tseslint.configs.recommended,

    // React best-practice rules from eslint-plugin-react.
    // (React version detection is configured later in `settings`.)
    reactPlugin.configs.flat.recommended,

    // React Hooks rules:
    // We enable the two canonical hooks rules directly to avoid legacy config/compat pitfalls.
    {
        plugins: {
            "react-hooks": reactHooks,
        },
        rules: {
            "react-hooks/rules-of-hooks": "error",
            "react-hooks/exhaustive-deps": "warn",
        },
    },

    // Prettier integration:
    // - runs Prettier as an ESLint rule (`prettier/prettier`)
    // - disables stylistic ESLint rules that conflict with Prettier
    //
    // NOTE: In many setups this is placed last. Here it is placed before the project block
    // so your explicit overrides (e.g. `quotes`) continue to win, matching your old config’s behavior.
    prettierRecommended,

    // Project-specific behavior and overrides.
    {
        plugins: {
            "react-refresh": reactRefresh,
            "unused-imports": unusedImports,
        },

        linterOptions: {
            // Report eslint-disable comments that no longer suppress anything.
            reportUnusedDisableDirectives: true,
        },

        languageOptions: {
            // Browser globals (window, document, etc.)
            globals: {
                ...globals.browser,
            },

            // Preserve the previous behavior of using the TypeScript parser.
            // (This keeps parsing/lint behavior consistent with your original config.)
            parser: tsParser,
        },

        settings: {
            // Let eslint-plugin-react detect the installed React version automatically.
            react: { version: "detect" },
        },

        rules: {
            // React Refresh: help ensure components are exported in a way compatible with fast refresh.
            "react-refresh/only-export-components": [
                "warn",
                { allowConstantExport: true },
            ],

            // Your TypeScript rule overrides.
            "@typescript-eslint/no-explicit-any": "off",

            // unused-imports: remove unused imports aggressively; warn on unused vars with underscore conventions.
            "unused-imports/no-unused-imports": "error",
            "unused-imports/no-unused-vars": [
                "warn",
                {
                    vars: "all",
                    varsIgnorePattern: "^_",
                    args: "after-used",
                    argsIgnorePattern: "^_",
                },
            ],

            // Enforce double quotes (this intentionally may differ from Prettier defaults).
            quotes: ["error", "double", { avoidEscape: true }],

            // Ensure formatting issues are reported as lint errors.
            // (The Prettier preset already enables this, but keeping it here preserves your explicit intent.)
            "prettier/prettier": ["error"],

            // Modern React doesn't require React in scope for JSX; keep this off.
            "react/react-in-jsx-scope": "off",
        },
    },
]);
