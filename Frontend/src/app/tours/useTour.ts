import { useContext } from "react";

import { TourContext } from "./TourContext";
import { TourContextValue } from "./types";

export const useTour = (): TourContextValue => {
    const context = useContext(TourContext);
    if (!context) throw new Error("useTour must be used inside TourProvider");
    return context;
};
