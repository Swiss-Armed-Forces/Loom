import { configureStore } from "@reduxjs/toolkit";
import { act, renderHook, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { ReactNode } from "react";
import { Provider } from "react-redux";
import {
    afterAll,
    afterEach,
    beforeAll,
    beforeEach,
    describe,
    expect,
    it,
} from "vitest";

import commonReducer from "@app/slices/commonSlice";
import searchReducer from "@app/slices/searchSlice";

import { useChatbot } from "./useChatbot";

const contexts = new Map<string, { contextId: string; hidden: boolean }>();

const CREATED_AT = "2026-01-01T00:00:00Z";

const contextIdOf = (url: string): string =>
    new URL(url).pathname.split("/").slice(-2)[0];

const server = setupServer(
    http.get(/\/api\/v1\/ai$/, () =>
        HttpResponse.json({
            contexts: [...contexts.values()]
                .filter((c) => !c.hidden)
                .map((c) => ({
                    context_id: c.contextId,
                    created_at: CREATED_AT,
                    question_count: 0,
                })),
        }),
    ),
    http.post(/\/api\/v1\/ai$/, () => {
        const contextId = `new-${contexts.size}`;
        contexts.set(contextId, { contextId, hidden: false });
        return HttpResponse.json({ context_id: contextId });
    }),
    http.get(/\/api\/v1\/ai\/([^/]+)\/history$/, ({ request }) => {
        const context = contexts.get(contextIdOf(request.url));
        if (!context)
            return HttpResponse.json({ detail: "gone" }, { status: 404 });
        return HttpResponse.json({
            created_at: CREATED_AT,
            questions: [],
            active_mode: "work",
            hidden: context.hidden,
        });
    }),
    http.patch(/\/api\/v1\/ai\/([^/]+)\/hidden$/, async ({ request }) => {
        const context = contexts.get(contextIdOf(request.url));
        if (!context)
            return HttpResponse.json({ detail: "gone" }, { status: 404 });
        const body = (await request.json()) as { hidden: boolean };
        context.hidden = body.hidden;
        return HttpResponse.json({ hidden: context.hidden });
    }),
);

const makeWrapper = () => {
    const store = configureStore({
        reducer: { search: searchReducer, common: commonReducer },
    });
    const wrapper = ({ children }: { children: ReactNode }) => (
        <Provider store={store}>{children}</Provider>
    );
    return { store, wrapper };
};

describe("useChatbot", () => {
    beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
    beforeEach(() => {
        contexts.clear();
        contexts.set("alpha", { contextId: "alpha", hidden: false });
        contexts.set("beta", { contextId: "beta", hidden: false });
    });
    afterEach(() => server.resetHandlers());
    afterAll(() => server.close());

    it("stays on the selected chat when the panel is closed and reopened", async () => {
        const { store, wrapper } = makeWrapper();
        const { result, rerender } = renderHook(
            ({ enabled }) => useChatbot(enabled),
            { wrapper, initialProps: { enabled: true } },
        );
        await waitFor(() =>
            expect(result.current.activeContext?.contextId).toBe("alpha"),
        );

        act(() => result.current.handleSelectContext("beta"));
        await waitFor(() =>
            expect(store.getState().search.activeContextId).toBe("beta"),
        );

        rerender({ enabled: false });
        rerender({ enabled: true });

        await waitFor(() =>
            expect(result.current.activeContext?.contextId).toBe("beta"),
        );
        expect(store.getState().search.activeContextId).toBe("beta");
    });

    it("comes back to the hidden chat the list no longer carries", async () => {
        const { wrapper } = makeWrapper();
        const first = renderHook(() => useChatbot(true), { wrapper });
        await waitFor(() =>
            expect(first.result.current.activeContext?.contextId).toBe("alpha"),
        );

        act(() => {
            first.result.current.handleHideActiveContext();
        });
        await waitFor(() => expect(first.result.current.isHidden).toBe(true));
        expect(
            first.result.current.filteredContexts.map((c) => c.contextId),
        ).toEqual(["beta"]);
        first.unmount();

        // A reload: the store kept the id, and the list no longer offers it.
        const second = renderHook(() => useChatbot(true), { wrapper });
        await waitFor(() =>
            expect(second.result.current.activeContext).toEqual({
                contextId: "alpha",
                hidden: true,
            }),
        );
    });
});
