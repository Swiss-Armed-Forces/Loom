import { useEffect, useRef } from "react";

import {
    subscribeChannel,
    unsubscribeChannel,
} from "@app/channelSubscriptions";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import { selectOpenFileTabs } from "@app/slices/searchSlice";

/**
 * Keep a websocket subscription open for every file that has a tab.
 *
 * Owned here rather than by the panels, because a panel only exists while the
 * File Detail pane is the one on screen: tabs restored from localStorage with
 * the sidebar last left on Statistics would otherwise never be subscribed, and
 * their `fileUpdate` messages would go unheard until the reader opened the
 * pane. Owned here rather than by `openFileTabThunk` as well, so that opening
 * a tab that is already open cannot raise a count nothing brings back down.
 *
 * Panels subscribe the file they are drawing on top of this. The counts are
 * ref-counted, so the overlap costs nothing.
 */
export const useOpenFileTabSubscriptions = () => {
    const dispatch = useAppDispatch();
    const openFileTabs = useAppSelector(selectOpenFileTabs);
    const subscribed = useRef<Set<string>>(new Set());

    useEffect(() => {
        const wanted = new Set(openFileTabs.map((tab) => tab.fileId));
        wanted.forEach((fileId) => {
            if (subscribed.current.has(fileId)) return;
            subscribed.current.add(fileId);
            subscribeChannel(fileId, dispatch);
        });
        subscribed.current.forEach((fileId) => {
            if (wanted.has(fileId)) return;
            subscribed.current.delete(fileId);
            unsubscribeChannel(fileId, dispatch);
        });
    }, [openFileTabs, dispatch]);

    // Release everything on unmount, so that a remount does not start from a
    // count this hook can no longer account for.
    useEffect(() => {
        const held = subscribed.current;
        return () => {
            held.forEach((fileId) => unsubscribeChannel(fileId, dispatch));
            held.clear();
        };
    }, [dispatch]);
};
