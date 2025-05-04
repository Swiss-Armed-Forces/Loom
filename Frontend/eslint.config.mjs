import { defineConfig, globalIgnores } from "eslint/config";
import { fixupConfigRules } from "@eslint/compat";
import reactRefresh from "eslint-plugin-react-refresh";
import unusedImports from "eslint-plugin-unused-imports";
import globals from "globals";
import tsParser from "@typescript-eslint/parser";
import path from "node:path";
import { fileURLToPath } from "node:url";
import js from "@eslint/js";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const compat = new FlatCompat({
    baseDirectory: __dirname,
    recommendedConfig: js.configs.recommended,
    allConfig: js.configs.all,
});

export default defineConfig([
    globalIgnores(["**/dist", "**/.eslintrc.cjs", "**/THIRD-PARTY.md"]),
    {
        extends: fixupConfigRules(
            compat.extends(
                "eslint:recommended",
                "plugin:@typescript-eslint/recommended",
                "plugin:react-hooks/recommended",
                "plugin:react/recommended",
                "plugin:prettier/recommended",
            ),
        ),

        plugins: {
            "react-refresh": reactRefresh,
            "unused-imports": unusedImports,
        },

        linterOptions: {
            reportUnusedDisableDirectives: true,
        },

        languageOptions: {
            globals: {
                ...globals.browser,
            },

            parser: tsParser,
        },

        settings: {
            react: {
                version: "detect",
            },
        },

        rules: {
            "react-refresh/only-export-components": [
                "warn",
                {
                    allowConstantExport: true,
                },
            ],

            "@typescript-eslint/no-explicit-any": "off",
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

            quotes: [
                "error",
                "double",
                {
                    avoidEscape: true,
                },
            ],

            "prettier/prettier": ["error"],
            "react/react-in-jsx-scope": "off",
        },
    },
]);
