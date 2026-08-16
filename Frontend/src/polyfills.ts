// Polyfills for APIs not universally available in older browsers.
//
// @vitejs/plugin-legacy handles most gaps via core-js at build time, but
// pdfjs-dist evaluates these APIs at module load time — before the legacy
// plugin's polyfill chunk is guaranteed to have run.  Importing this file as
// the very first module in main.tsx ensures they are in place early enough.
// This also covers dev mode, where the legacy plugin applies no polyfills.
import "core-js/proposals/promise-try";
import "core-js/proposals/map-upsert-v4";
import "core-js/proposals/array-buffer-base64";
