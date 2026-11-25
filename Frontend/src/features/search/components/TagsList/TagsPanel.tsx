import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { loadTags } from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import { selectTags, setTags } from "@app/slices/searchSlice";
import { FilterBar } from "@features/search/components/FilterBar/FilterBar";

import { TagsList } from "./TagsList";
import styles from "./TagsPanel.module.css";

const TAGS_REFRESH_MS = 5_000;

/**
 * The sidebar's tag panel: every tag in the index, narrowed by name.
 *
 * Filtering here is a substring test over a list already in hand, so it needs no
 * request and has no paging, loading or failure of its own — unlike the folder
 * panel's filter, which is a search. Each panel owning its own filter is what lets
 * the two differ that much behind bars that look alike.
 */
export const TagsPanel = () => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();
    const tags = useAppSelector(selectTags);
    const [filter, setFilter] = useState("");

    const fetchTags = useCallback(async () => {
        try {
            dispatch(setTags(await loadTags()));
        } catch (error) {
            toast.error(`Error loading tags: ${error}`);
        }
    }, [dispatch]);

    useEffect(() => {
        fetchTags();
        const interval = setInterval(fetchTags, TAGS_REFRESH_MS);
        return () => clearInterval(interval);
    }, [fetchTags]);

    const visibleTags = useMemo(
        () =>
            filter
                ? tags.filter((tag) =>
                      tag.toLowerCase().includes(filter.toLowerCase()),
                  )
                : tags,
        [tags, filter],
    );

    return (
        <div className={styles.tagsPanel}>
            <FilterBar
                value={filter}
                onChange={setFilter}
                placeholder={t("sideMenu.tagsFilterPlaceholder")}
            />
            <div className={styles.tagListContainer}>
                <TagsList tags={visibleTags} />
            </div>
        </div>
    );
};
