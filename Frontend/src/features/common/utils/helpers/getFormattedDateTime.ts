import { format, parseISO } from "date-fns";

/**
 * Year, month, day - the order the rest of the pattern implies.
 *
 * `yyyy-dd-MM` reads as an ISO date and is not one, so every date in the first
 * twelve days of a month comes out plausible and wrong rather than visibly so.
 */
export const getFormattedDateTime = (inputDate: string) => {
    const date = parseISO(inputDate);
    return format(date, "yyyy-MM-dd HH:mm");
};
