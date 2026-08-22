/*
 * Dynamically injects highlight.js GitHub themes wrapped in @media blocks
 * so the correct theme is applied based on the user's color-scheme preference.
 *
 * Vite's CSS bundler silently strips @import media conditions, so we import
 * the raw CSS strings and inject them inside proper @media queries at runtime.
 */

import githubDark from "highlight.js/styles/github-dark.css?raw";
import githubLight from "highlight.js/styles/github.css?raw";

const STYLE_ID = "hljs-color-scheme";
if (!document.getElementById(STYLE_ID)) {
    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = `
@media (prefers-color-scheme: light) {
${githubLight}
}
@media (prefers-color-scheme: dark) {
${githubDark}
}
`;
    document.head.appendChild(style);
}
