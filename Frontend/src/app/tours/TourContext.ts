import { createContext } from "react";

import { TourContextValue } from "./types";

export const TourContext = createContext<TourContextValue | null>(null);
