// Promise.try is ES2025 and not yet available in all browsers.
// pdfjs-dist@6.x uses it internally, so we polyfill it here before any
// other module is evaluated.
if (typeof (Promise as any).try !== "function") {
    (Promise as any).try = function <T>(
        fn: (...args: any[]) => T,
        ...args: any[]
    ): Promise<T> {
        return new Promise<T>((resolve) => resolve(fn(...args)));
    };
}
