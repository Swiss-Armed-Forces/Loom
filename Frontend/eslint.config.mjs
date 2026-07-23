import { defineConfig, globalIgnores } from "eslint/config";
import js from "@eslint/js";
import globals from "globals";

import tsParser from "@typescript-eslint/parser";
import tseslint from "typescript-eslint";

import reactPlugin from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";

import reactRefresh from "eslint-plugin-react-refresh";
import unusedImports from "eslint-plugin-unused-imports";
import importPlugin from "eslint-plugin-import";

import prettierRecommended from "eslint-plugin-prettier/recommended";

export default defineConfig([
    // Ignore generated artifacts and non-source files we don't want to lint.
    globalIgnores(["dist/", "dist-demo/", "**/THIRD-PARTY.md"]),

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
        // Only applies to source file
        files: ["src/**/*.{ts,tsx}"],
        plugins: {
            "react-refresh": reactRefresh,
            "unused-imports": unusedImports,
            import: importPlugin,
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

            // Add parser options for TypeScript project for imports
            parserOptions: {
                projectService: true,
                ecmaFeatures: {
                    jsx: true,
                },
            },
        },

        settings: {
            // Let eslint-plugin-react detect the installed React version automatically.
            react: { version: "detect" },

            // TS import resolver configuration
            "import/resolver": {
                typescript: {
                    alwaysTryTypes: true,
                    project: "./tsconfig.json",
                },
                node: {
                    extensions: [".js", ".jsx", ".ts", ".tsx", ".css"],
                },
            },
        },

        rules: {
            // React Refresh: help ensure components are exported in a way compatible with fast refresh.
            "react-refresh/only-export-components": [
                "warn",
                { allowConstantExport: true },
            ],

            // Enforce arrow functions for React components
            "react/function-component-definition": [
                "error",
                {
                    namedComponents: "arrow-function",
                    unnamedComponents: "arrow-function",
                },
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

            // Disallow file extensions in imports
            "import/extensions": [
                "error",
                "ignorePackages",
                {
                    js: "never",
                    jsx: "never",
                    ts: "never",
                    tsx: "never",
                },
            ],

            // Enforce double quotes (this intentionally may differ from Prettier defaults).
            quotes: ["error", "double", { avoidEscape: true }],

            // Prefer const for component declarations
            "prefer-const": "error",

            // Ensure formatting issues are reported as lint errors.
            // (The Prettier preset already enables this, but keeping it here preserves your explicit intent.)
            "prettier/prettier": ["error"],

            // Modern React doesn't require React in scope for JSX; keep this off.
            "react/react-in-jsx-scope": "off",

            // Disallow function declarations
            "func-style": ["error", "expression"],

            // Import rules (optional but recommended)
            "import/no-unresolved": "error",
            "import/order": [
                "error",
                {
                    groups: [
                        "builtin",
                        "external",
                        "internal",
                        "parent",
                        "sibling",
                        "index",
                    ],
                    "newlines-between": "always",
                    alphabetize: {
                        order: "asc",
                        caseInsensitive: true,
                    },
                },
            ],

            "@typescript-eslint/naming-convention": [
                "error",
                {
                    selector: "typeLike",
                    format: ["PascalCase"],
                },
                {
                    selector: "variable",
                    format: ["camelCase", "UPPER_CASE", "PascalCase"],
                    leadingUnderscore: "allow",
                },
                {
                    selector: "function",
                    format: ["camelCase", "PascalCase"], // PascalCase for React components
                },
                {
                    selector: "parameter",
                    format: ["camelCase", "PascalCase"],
                    leadingUnderscore: "allow",
                    trailingUnderscore: "allow",
                },
                {
                    selector: "parameter",
                    filter: {
                        regex: "^_+$", // Allows _, __, ___, etc.
                        match: true,
                    },
                    format: null, // Disable format check for these
                },
            ],
        },
    },
    {
        // Only applies to config files
        files: ["*.config.{js,mjs,ts}", "vite.config.ts"],
        languageOptions: {
            globals: {
                ...globals.node,
            },
            parser: tsParser,
        },
        settings: {
            // Let eslint-plugin-react detect the installed React version automatically.
            react: { version: "detect" },
        },
        rules: {
            "@typescript-eslint/no-require-imports": "off",
            "import/no-unresolved": "off", // Config files may have special imports
        },
    },
]);
