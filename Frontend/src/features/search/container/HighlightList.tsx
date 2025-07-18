import {
    Accordion,
    AccordionDetails,
    AccordionSummary,
    IconButton,
    ListItemIcon,
    ListItemText,
    Menu,
    MenuItem,
    Typography,
    TypographyProps,
    styled,
} from "@mui/material";
import { ExpandMore, MoreVert, Search, Sort } from "@mui/icons-material";
import { HighlightContent } from "./HighlightContent";
import styles from "./HighlightList.module.css";
import { FC, Fragment, ReactNode, useState } from "react";
import { updateFieldOfQuery } from "../SearchQueryUtils";
import { useAppDispatch, useAppSelector } from "../../../app/hooks";
import { updateQuery, selectQuery } from "../searchSlice";
import { useTranslation } from "react-i18next";

type HighlightItem = [string, string[]];

const FieldTypography = styled(Typography)<TypographyProps>`
    line-height: 2.5;
`;

const PATTERN_HIGHLIGHT_TAG = /<\/?highlight>/g;

const priorities = [
    /^full_name$/,
    /^short_name$/,
    /^content/,
    /^libretranslate_translations/,
    null, // All other elements are placed here
    /^tika_meta/,
    /^tasks/,
];

const defaultExpanded = [/^content/, /^libretranslate_translations/];

const isDefaultExpanded = (field: string) =>
    defaultExpanded.some((isExpanded) => isExpanded.test(field));

const getHighlightPriority = (key: string): number => {
    let fallbackPrio = 9999;
    let currentItemPrio = 0;
    for (const prio of priorities) {
        currentItemPrio++;
        if (prio === null) {
            fallbackPrio = currentItemPrio;
            continue;
        }
        if (prio.test(key)) {
            return currentItemPrio;
        }
    }
    return fallbackPrio;
};

const sortHighlightsByPriority = (
    [aKey]: HighlightItem,
    [bKey]: HighlightItem,
): number => {
    const aPrio = getHighlightPriority(aKey);
    const bPrio = getHighlightPriority(bKey);
    if (aPrio < bPrio) {
        return -1;
    }
    if (aPrio > bPrio) {
        return 1;
    }

    return aKey.localeCompare(bKey);
};

/**
 * ES highlighting automatically adds custom tags to notify us.
 * There is no way to retrieve this field value as well
 * as the highlighting information without overhead,
 * so we're just stripping those tags here.
 *
 * @param value the value to sanitise
 * @returns the value for use in the query
 */
function sanitiseFieldValue(value: string | undefined): string | undefined {
    return value?.replace(PATTERN_HIGHLIGHT_TAG, "")?.replace(/"/g, '\\"');
}

/**
 * ES does not allow certain characters in the field names to go unescaped.
 *
 * @param value the value to sanitise
 */
function sanitiseFieldNameForQuery(value: string): string {
    return value.replace(/([-\s\\:])/g, "\\$1");
}

interface HighlightEntryProps {
    field: string;
    value: string[];
    onContextMenu: (button: HTMLElement, field: string) => void;
    fullDetails?: boolean;
}

export const HighlightEntry: FC<HighlightEntryProps> = ({
    field,
    value,
    onContextMenu,
    fullDetails,
}) => {
    const [expanded, setExpanded] = useState<boolean>(
        fullDetails || isDefaultExpanded(field),
    );

    const valueElement = value.map((val) => {
        const parts: (string | ReactNode)[] = [];

        let result: RegExpExecArray | null = PATTERN_HIGHLIGHT_TAG.exec(val);
        let lastIndex = 0;
        let endIndex = val.length;

        // The result only oscillates between highlighted and non-highlighted text.
        // However, we also handle zero-width segments.
        let highlighting = false;
        while (result) {
            endIndex = result.index + result[0].length;
            const formatted = val.substring(lastIndex, result.index);

            parts.push(highlighting ? <em>{formatted}</em> : formatted);

            lastIndex = endIndex;
            highlighting = !highlighting;

            result = PATTERN_HIGHLIGHT_TAG.exec(val);
        }
        parts.push(val.substring(endIndex));

        return (
            <>
                {parts.map((p, index) => (
                    <Fragment key={index}>{p}</Fragment>
                ))}
            </>
        );
    });

    return (
        <Accordion
            TransitionProps={{ timeout: 0 }}
            key={field}
            expanded={expanded}
            onChange={() => {
                setExpanded(!expanded);
            }}
            className={styles.accordion}
        >
            <div className={styles.accordionHeader}>
                <IconButton
                    onClick={(event) => {
                        event.stopPropagation();
                        onContextMenu(event.currentTarget, field);
                    }}
                >
                    <MoreVert />
                </IconButton>
                <AccordionSummary expandIcon={<ExpandMore />}>
                    <FieldTypography className={styles.hitField}>
                        {field}
                    </FieldTypography>
                    <FieldTypography
                        color="text.secondary"
                        className={styles.resultHighlightText}
                    >
                        {!expanded && valueElement[0]}
                    </FieldTypography>
                </AccordionSummary>
            </div>
            <AccordionDetails>
                {valueElement.map((highlight, index) => {
                    return (
                        <HighlightContent key={index} highlight={highlight} />
                    );
                })}
            </AccordionDetails>
        </Accordion>
    );
};

export interface HighlightListProps {
    highlights: Record<string, string[]>;
    fullDetails?: boolean;
}

export const HighlightList: FC<HighlightListProps> = ({
    highlights,
    fullDetails,
}) => {
    const { t } = useTranslation();
    const query = useAppSelector(selectQuery);
    const dispatch = useAppDispatch();
    const [fieldInteractionMenuAnchor, setFieldInteractionMenuAnchor] =
        useState<HTMLElement | undefined>();

    const [contextField, setContextField] = useState<string | undefined>();

    if (!highlights) return;

    const highlightValues: Record<string, string> = Object.entries(highlights)
        .map(([field, value]) => [field, sanitiseFieldValue(value[0])])
        .reduce(
            (previous, [field, value]) => ({
                ...previous,
                [field ?? "unknown"]: value,
            }),
            {},
        );

    const onContextMenuOpen = (target: HTMLElement, field: string) => {
        setFieldInteractionMenuAnchor(target);
        setContextField(field);
    };
    const onContextMenuClose = () => {
        setFieldInteractionMenuAnchor(undefined);
        setContextField(undefined);
    };

    const onSearchForField = () => {
        if (!contextField) return;
        const updatedQuery = updateFieldOfQuery(
            query?.query ?? "",
            sanitiseFieldNameForQuery(contextField),
            highlightValues[contextField] ?? "",
        );
        dispatch(
            updateQuery({
                query: updatedQuery,
            }),
        );
    };
    const onSortOnField = () => {
        if (!contextField) return;
        dispatch(
            updateQuery({
                sortField: contextField,
            }),
        );
    };

    return (
        <>
            {Object.entries(highlights)
                .sort(sortHighlightsByPriority)
                .map(([field, value]) => (
                    <HighlightEntry
                        key={field}
                        field={field}
                        value={value}
                        onContextMenu={onContextMenuOpen}
                        fullDetails={fullDetails}
                    />
                ))}
            <Menu
                anchorEl={fieldInteractionMenuAnchor}
                open={!!fieldInteractionMenuAnchor}
                onClose={onContextMenuClose}
            >
                <MenuItem onClick={onSearchForField}>
                    <ListItemIcon>
                        <Search />
                    </ListItemIcon>
                    <ListItemText>
                        {t("generalSearchView.queryThisField")}
                    </ListItemText>
                </MenuItem>
                <MenuItem onClick={onSortOnField}>
                    <ListItemIcon>
                        <Sort />
                    </ListItemIcon>
                    <ListItemText>
                        {t("generalSearchView.sortThisField")}
                    </ListItemText>
                </MenuItem>
            </Menu>
        </>
    );
};
