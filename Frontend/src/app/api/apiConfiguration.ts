import { Configuration } from "./generated";

const normalizeBaseUrl = (baseUrl: string): string =>
    baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`;

export const buildApiBasePath = (origin: string, baseUrl: string): string =>
    new URL(
        "api",
        new URL(normalizeBaseUrl(baseUrl), `${origin.replace(/\/$/, "")}/`),
    )
        .toString()
        .replace(/\/$/, "");

export const buildWebSocketApiBasePath = (
    origin: string,
    baseUrl: string,
): string => {
    const url = new URL(buildApiBasePath(origin, baseUrl));
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    return url.toString().replace(/\/$/, "");
};

export const apiConfiguration = new Configuration({
    basePath: buildApiBasePath(
        window.location.origin,
        import.meta.env.BASE_URL,
    ),
});
