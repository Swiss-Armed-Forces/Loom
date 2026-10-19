import { useDispatch, useSelector, useStore } from "react-redux";

import type { RootState, AppDispatch, AppStore } from "./store";

// Use throughout your app instead of plain `useDispatch` and `useSelector`
export const useAppDispatch = useDispatch.withTypes<AppDispatch>();
export const useAppSelector = useSelector.withTypes<RootState>();
// Read state without subscribing to it. Use when a value is only needed
// inside a callback or effect, never during render.
export const useAppStore = useStore.withTypes<AppStore>();
