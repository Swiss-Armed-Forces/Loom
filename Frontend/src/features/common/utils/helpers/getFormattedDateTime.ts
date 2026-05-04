import { format, parseISO } from "date-fns";

export const getFormattedDateTime = (inputDate: string) => {
    const date = parseISO(inputDate);
    return format(date, "yyyy-dd-MM HH:mm");
};
