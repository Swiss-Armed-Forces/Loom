import { Search, Sort } from "@mui/icons-material";
import { ListItemIcon, ListItemText, Menu, MenuItem } from "@mui/material";
import { useState, useMemo, useCallback } from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import { updateQuery, selectQuery } from "@app/slices/searchSlice";
import { updateFieldOfQuery } from "@features/common/utils/helpers";

import { HighlightItem } from "./HighlightItem";

type HighlightItem = [string, string[]];
const STRIP_TAGS = /<\/?highlight>/g;

const PRIORITIES = [
    /^full_name$/,
    /^short_name$/,
    /^content/,
    /^libretranslate_translations/,
    null, // Fallback for unmatched fields
    /^tika_meta/,
    /^tasks/,
];

const getHighlightPriority = (key: string): number => {
    let fallbackPrio = 9999;
    for (let i = 0; i < PRIORITIES.length; i++) {
        const prio = PRIORITIES[i];
        if (prio === null) fallbackPrio = i;
        else if (prio.test(key)) return i;
    }
    return fallbackPrio;
};

const sortHighlightsByPriority = (
    a: HighlightItem,
    b: HighlightItem,
): number => {
    const aPrio = getHighlightPriority(a[0]);
    const bPrio = getHighlightPriority(b[0]);
    return aPrio !== bPrio ? aPrio - bPrio : a[0].localeCompare(b[0]);
};

export interface HighlightListProps {
    highlights: Record<string, string[]>;
    fullDetails?: boolean;
}

export const HighlightList = ({
    highlights,
    fullDetails,
}: HighlightListProps) => {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const query = useAppSelector(selectQuery);

    const [menuAnchor, setMenuAnchor] = useState<HTMLElement | null>(null);
    const [activeField, setActiveField] = useState<string | null>(null);

    // Sort highlights only when data changes
    const sortedEntries = useMemo(
        () => Object.entries(highlights ?? {}).sort(sortHighlightsByPriority),
        [highlights],
    );

    // Pre-calculate clean values for search queries
    const cleanValues = useMemo(() => {
        const mapping: Record<string, string> = {};
        Object.entries(highlights ?? {}).forEach(([field, val]) => {
            mapping[field] = val[0]?.replace(STRIP_TAGS, "") ?? "";
        });
        return mapping;
    }, [highlights]);

    const handleMenuOpen = useCallback((target: HTMLElement, field: string) => {
        setMenuAnchor(target);
        setActiveField(field);
    }, []);

    const handleMenuClose = () => {
        setMenuAnchor(null);
        setActiveField(null);
    };

    const handleSearch = () => {
        if (!activeField) return;
        dispatch(
            updateQuery({
                query: updateFieldOfQuery(
                    query?.query ?? "",
                    activeField,
                    cleanValues[activeField],
                ),
            }),
        );
        handleMenuClose();
    };

    const handleSort = () => {
        if (!activeField) return;
        dispatch(updateQuery({ sortField: activeField }));
        handleMenuClose();
    };

    if (!highlights) return null;

    return (
        <>
            {sortedEntries.map(([field, value]) => (
                <HighlightItem
                    key={field}
                    field={field}
                    value={value}
                    onContextMenu={handleMenuOpen}
                    fullDetails={fullDetails}
                />
            ))}

            <Menu
                anchorEl={menuAnchor}
                open={Boolean(menuAnchor)}
                onClose={handleMenuClose}
            >
                <MenuItem onClick={handleSearch}>
                    <ListItemIcon>
                        <Search fontSize="small" />
                    </ListItemIcon>
                    <ListItemText>
                        {t("generalSearchView.queryThisField")}
                    </ListItemText>
                </MenuItem>
                <MenuItem onClick={handleSort}>
                    <ListItemIcon>
                        <Sort fontSize="small" />
                    </ListItemIcon>
                    <ListItemText>
                        {t("generalSearchView.sortThisField")}
                    </ListItemText>
                </MenuItem>
            </Menu>
        </>
    );
};
