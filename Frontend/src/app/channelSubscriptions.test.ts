import { beforeEach, describe, expect, it, vi } from "vitest";

import {
    resetChannelSubscriptions,
    subscribeChannel,
    unsubscribeChannel,
} from "./channelSubscriptions";

const messagesOf = (dispatch: ReturnType<typeof vi.fn>) =>
    dispatch.mock.calls.map(
        ([action]) =>
            `${action.message.message.type}:${[...action.message.message.channels].join(",")}`,
    );

describe("channel subscriptions", () => {
    beforeEach(() => {
        vi.useFakeTimers();
        resetChannelSubscriptions();
    });

    it("keeps the channel when a card leaves and comes straight back", () => {
        const dispatch = vi.fn();
        subscribeChannel("f1", dispatch);
        unsubscribeChannel("f1", dispatch);
        vi.advanceTimersByTime(500);
        subscribeChannel("f1", dispatch);
        vi.advanceTimersByTime(10_000);
        expect(messagesOf(dispatch)).toEqual(["subscribe:f1"]);
    });

    it("releases a channel nothing came back for", () => {
        const dispatch = vi.fn();
        subscribeChannel("f1", dispatch);
        unsubscribeChannel("f1", dispatch);
        vi.advanceTimersByTime(10_000);
        expect(messagesOf(dispatch)).toEqual([
            "subscribe:f1",
            "unsubscribe:f1",
        ]);
    });

    it("holds the channel while another view still wants it", () => {
        const dispatch = vi.fn();
        subscribeChannel("f1", dispatch);
        subscribeChannel("f1", dispatch);
        unsubscribeChannel("f1", dispatch);
        vi.advanceTimersByTime(10_000);
        expect(messagesOf(dispatch)).toEqual(["subscribe:f1"]);
    });
});
