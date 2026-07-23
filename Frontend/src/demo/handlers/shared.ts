import { HttpResponse, type JsonBodyType } from "msw";

export type JsonObject = Record<string, unknown>;

export type ParsedBody =
    | { ok: true; value: JsonObject }
    | { ok: false; response: Response };

export const json = (body: unknown, status = 200): Response =>
    HttpResponse.json(body as JsonBodyType, { status });

export const empty = (status = 204): Response =>
    new HttpResponse(null, { status });

export const error = (detail: string, status: number): Response =>
    json({ detail }, status);

export const parseBody = async (request: Request): Promise<ParsedBody> => {
    try {
        const value: unknown = await request.json();
        if (value && typeof value === "object" && !Array.isArray(value))
            return { ok: true, value: value as JsonObject };
    } catch {
        // The response below deliberately mirrors FastAPI validation failures.
    }
    return {
        ok: false,
        response: error("Request body must be a JSON object", 422),
    };
};

export const objectValue = (
    value: unknown,
): Record<string, unknown> | undefined =>
    value && typeof value === "object" && !Array.isArray(value)
        ? (value as Record<string, unknown>)
        : undefined;

export const stringValue = (value: unknown): string | undefined =>
    typeof value === "string" ? value : undefined;

export const stringArrayValue = (value: unknown): string[] | undefined =>
    Array.isArray(value) && value.every((item) => typeof item === "string")
        ? value
        : undefined;

export const queryFromUrl = (url: URL): string =>
    url.searchParams.get("search_string") || "*";

export const demoPath = (request: Request): string =>
    new URL(request.url).pathname.replace(/^.*\/api/, "");
