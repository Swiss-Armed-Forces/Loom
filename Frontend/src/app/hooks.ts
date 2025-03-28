import { useDispatch, useSelector } from "react-redux";
import type { RootState, AppDispatch } from "./store";
import { useEffect, useState } from "react";

// Use throughout your app instead of plain `useDispatch` and `useSelector`
export const useAppDispatch = useDispatch.withTypes<AppDispatch>();
export const useAppSelector = useSelector.withTypes<RootState>();

// Custom hook for responsive design

/**
 *
 * @param pixelNumber number of pixel to check
 * @returns true if the window is smaller of pixelNumber
 */
export const useMatchMedia = (pixelNumber: number) => {
    const mediaQuery = `(max-width: ${pixelNumber}px)`;
    const [match, setMatch] = useState(true);

    useEffect(() => {
        const check = window.matchMedia(mediaQuery);
        setMatch(check.matches);
        const listener = (matches: any) => {
            setMatch(matches.matches);
        };
        check.addEventListener("change", listener);

        return () => {
            return check.removeEventListener("change", listener);
        };
    }, [mediaQuery]);
    return match;
};
