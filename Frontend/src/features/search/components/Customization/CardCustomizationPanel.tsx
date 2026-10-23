import {
    Add,
    DensityLarge,
    DensityMedium,
    DensitySmall,
    Remove,
    ViewColumnOutlined,
    ViewHeadlineOutlined,
} from "@mui/icons-material";
import {
    Box,
    Chip,
    Divider,
    IconButton,
    List,
    ListItem,
    ListItemText,
    Menu,
    Slider,
    MenuItem,
    Switch,
    ToggleButton,
    ToggleButtonGroup,
    Tooltip,
    Typography,
} from "@mui/material";
import { Fragment, ReactNode, useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { getPreviewFields, PreviewField } from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    CardPreset,
    THUMBNAIL_WIDTH_MAX_REM,
    THUMBNAIL_WIDTH_STEP_REM,
    FieldLayout,
    applyCardPreset,
    selectAvailablePreviewFields,
    selectCardElementVisibility,
    selectFieldLayout,
    selectMatchingCardPreset,
    addFieldColumn,
    MAX_FIELD_COLUMNS,
    removeFieldColumn,
    selectBoldPreviewFields,
    selectFieldColumnCount,
    selectFieldColumnOf,
    selectPreviewFields,
    selectShowFieldNames,
    selectThumbnailWidthRem,
    setAvailablePreviewFields,
    setFieldLayout,
    setPreviewFields,
    toggleBoldPreviewField,
    setShowActions,
    setShowAttachments,
    setShowFieldNames,
    setShowExtensionIcon,
    setShowFieldActions,
    setShowFilePath,
    setShowHighlights,
    setShowParentNavigation,
    setShowSortIndicator,
    setShowStatusIndicators,
    setShowTags,
    setThumbnailWidthRem,
} from "@app/slices/searchSlice";
import { indicatorPreviewFields } from "@features/search/components/FieldList/indicatorFields";
import { useFieldReorder } from "@features/search/hooks/useFieldReorder";

/** The element presets, in the order they read: fewest elements first. */
const PRESET_OPTIONS: {
    value: CardPreset;
    icon: React.ReactNode;
    labelKey: string;
}[] = [
    {
        value: "compact",
        icon: <DensitySmall />,
        labelKey: "toolbar.cardPreset.compact",
    },
    {
        value: "standard",
        icon: <DensityMedium />,
        labelKey: "toolbar.cardPreset.standard",
    },
    {
        value: "full",
        icon: <DensityLarge />,
        labelKey: "toolbar.cardPreset.full",
    },
];

/* A zone is a drop target as well as a list, so it keeps a visible box even
while it holds nothing - an empty column has to be somewhere a chip can be
dropped. */
const FIELD_ZONE_SX = {
    mx: 1.5,
    mt: 1,
    px: 1,
    pt: 0.5,
    pb: 1,
    minHeight: 56,
    border: "1px dashed",
    borderColor: "divider",
    borderRadius: 1,
    display: "flex",
    flexWrap: "wrap",
    gap: 0.5,
    alignItems: "flex-start",
    alignContent: "flex-start",
} as const;
const FIELD_ZONE_LABEL_SX = { width: "100%" } as const;
const FIELD_SETTING_ROW_SX = {
    px: 1.5,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
} as const;
const FIELD_ADD_SPACER_SX = { flex: 1 } as const;
/* The line layout has one list, not one per column, so its chips sit in a
plain row rather than in drop zones. */
const FIELD_LIST_SX = {
    px: 1.5,
    pt: 1,
    display: "flex",
    flexWrap: "wrap",
    gap: 0.5,
    alignItems: "center",
} as const;
const FIELD_ADD_ROW_SX = {
    px: 1.5,
    py: 1,
    display: "flex",
    alignItems: "center",
} as const;

const FIELD_LAYOUT_OPTIONS: {
    value: FieldLayout;
    icon: React.ReactNode;
    labelKey: string;
}[] = [
    {
        value: "compact",
        icon: <ViewHeadlineOutlined />,
        labelKey: "sideMenu.customization.fieldLayoutCompact",
    },
    {
        value: "line",
        icon: <ViewColumnOutlined />,
        labelKey: "sideMenu.customization.fieldLayoutLine",
    },
];

/** One labelled row of the display section: a caption and the control it
 *  names. */
/* Narrow enough to sit where a switch sits, so the row reads as one of the
element rows it is among. */
const THUMBNAIL_SLIDER_SX = { width: 110 } as const;

const SettingRow = ({
    label,
    children,
}: {
    label: string;
    children: ReactNode;
}) => (
    <Box
        sx={{
            px: 2,
            pb: 0.5,
            display: "flex",
            alignItems: "center",
            gap: 1,
        }}
    >
        <Typography
            variant="caption"
            color="text.secondary"
            sx={{ flex: "0 0 4.5rem" }}
        >
            {label}
        </Typography>
        {children}
    </Box>
);

export const CardCustomizationPanel = () => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();
    const availableFields = useAppSelector(selectAvailablePreviewFields);
    const previewFields = useAppSelector(selectPreviewFields);
    const boldFields = useAppSelector(selectBoldPreviewFields);
    const columnCount = useAppSelector(selectFieldColumnCount);
    const columnOf = useAppSelector(selectFieldColumnOf);
    const showFieldNames = useAppSelector(selectShowFieldNames);
    const thumbnailWidthRem = useAppSelector(selectThumbnailWidthRem);
    const selectedPreset = useAppSelector(selectMatchingCardPreset);
    const fieldLayout = useAppSelector(selectFieldLayout);
    const vis = useAppSelector(selectCardElementVisibility);
    const [error, setError] = useState<string | null>(null);
    const [addAnchorEl, setAddAnchorEl] = useState<HTMLElement | null>(null);
    const { dragProps, zoneProps, isDragging, isDropTarget } =
        useFieldReorder();

    const fetchFields = useCallback(async () => {
        try {
            const fields = await getPreviewFields();
            // Offered beside the backend's own, and chosen the same way; the
            // card draws them from the preview rather than asking for them.
            dispatch(
                setAvailablePreviewFields([
                    ...fields,
                    ...indicatorPreviewFields(t),
                ]),
            );
            setError(null);
        } catch (err) {
            setError(String(err));
        }
    }, [dispatch, t]);

    useEffect(() => {
        fetchFields();
    }, [fetchFields]);

    const handlePreviewFieldToggle = (fieldId: string) => {
        const next = previewFields.includes(fieldId)
            ? previewFields.filter((f) => f !== fieldId)
            : [...previewFields, fieldId];
        dispatch(setPreviewFields(next));
    };

    // Walked in selection order, not in the order the API lists the fields:
    // the selection is the order the columns are drawn in, and a chip that
    // does not sit where its column does is not a label for it.
    const selectedFields = previewFields.flatMap((id) => {
        const field = availableFields.find((f) => f.id === id);
        return field ? [field] : [];
    });
    // Both columns draw their own members in the one selection order, so a
    // field keeps its place relative to the rest of its column whichever side
    // it is on.
    const fieldsIn = (column: number) =>
        selectedFields.filter(
            (f) => Math.min(columnOf[f.id] ?? 0, columnCount - 1) === column,
        );
    const unselectedFields = availableFields.filter(
        (f) => !previewFields.includes(f.id),
    );

    /*
     * In preset order: what "compact" draws, then what "standard" adds, then
     * what only "full" does. A reader comparing the presets with the switches
     * is reading one list against the other, so the two agree.
     */
    const displayToggles: {
        label: string;
        checked: boolean;
        action: (v: boolean) => void;
    }[] = [
        // Compact.
        {
            label: t("sideMenu.fields.extensionIcon"),
            checked: vis.showExtensionIcon,
            action: (v) => dispatch(setShowExtensionIcon(v)),
        },
        {
            label: t("sideMenu.fields.filePath"),
            checked: vis.showFilePath,
            action: (v) => dispatch(setShowFilePath(v)),
        },
        // Standard adds these - and the thumbnail slider, which the list
        // renders between the two groups.
        {
            label: t("sideMenu.fields.highlights"),
            checked: vis.showHighlights,
            action: (v) => dispatch(setShowHighlights(v)),
        },
        {
            label: t("sideMenu.fields.parentNavigation"),
            checked: vis.showParentNavigation,
            action: (v) => dispatch(setShowParentNavigation(v)),
        },
        {
            label: t("sideMenu.fields.statusIndicators"),
            checked: vis.showStatusIndicators,
            action: (v) => dispatch(setShowStatusIndicators(v)),
        },
        {
            label: t("sideMenu.fields.attachments"),
            checked: vis.showAttachments,
            action: (v) => dispatch(setShowAttachments(v)),
        },
        {
            label: t("sideMenu.fields.tags"),
            checked: vis.showTags,
            action: (v) => dispatch(setShowTags(v)),
        },
        // Full only.
        {
            label: t("sideMenu.fields.actions"),
            checked: vis.showActions,
            action: (v) => dispatch(setShowActions(v)),
        },
        {
            label: t("sideMenu.fields.sortIndicator"),
            checked: vis.showSortIndicator,
            action: (v) => dispatch(setShowSortIndicator(v)),
        },
        {
            label: t("sideMenu.fields.fieldActions"),
            checked: vis.showFieldActions,
            action: (v) => dispatch(setShowFieldActions(v)),
        },
    ];

    /** Where the thumbnail slider sits: the first thing "standard" adds. */
    const THUMBNAIL_ROW_INDEX = 2;

    /**
     * One selected field.
     *
     * `column` is the card column the chip sits in, and is passed to the drag
     * so that dropping it in another zone moves the field there. The line
     * layout has one list and passes none: a drop there is a reorder.
     */
    const renderChip = (field: PreviewField, column?: number) => {
        // The index the drag speaks in is the position in the whole
        // selection, not in this column: one order underlies both.
        const index = previewFields.indexOf(field.id);
        return (
            <Tooltip
                key={field.id}
                title={t("sideMenu.customization.chipHint")}
            >
                <Chip
                    label={field.label}
                    size="small"
                    onClick={() => dispatch(toggleBoldPreviewField(field.id))}
                    onDelete={() => handlePreviewFieldToggle(field.id)}
                    {...dragProps(index, column)}
                    sx={{
                        cursor: "grab",
                        opacity: isDragging(index) ? 0.4 : 1,
                        // The chip says on itself what it does to the card,
                        // so the two cannot disagree.
                        fontWeight: boldFields.includes(field.id)
                            ? "bold"
                            : undefined,
                        boxShadow: isDropTarget(index)
                            ? (theme) =>
                                  `inset 2px 0 0 ${theme.palette.primary.main}`
                            : undefined,
                    }}
                />
            </Tooltip>
        );
    };

    if (error) {
        return (
            <Typography variant="body2" color="error" sx={{ p: 2 }}>
                {t("sideMenu.fields.error")}
            </Typography>
        );
    }

    if (availableFields.length === 0) {
        return (
            <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
                {t("sideMenu.fields.loading")}
            </Typography>
        );
    }

    return (
        <>
            {/* ── Section 1: Card Display ──────────────────────── */}
            <Box data-tour="customization-card-display">
                <Typography
                    variant="subtitle2"
                    sx={{ px: 2, pt: 1.5, pb: 0.5 }}
                >
                    {t("sideMenu.customization.cardDisplay")}
                </Typography>

                {/* A shortcut to the whole row of switches below. Nothing is
                selected here once they have been taken somewhere no preset
                describes - the row reports what the card reads as rather than
                holding a mode of its own. */}
                <SettingRow label={t("sideMenu.customization.preset")}>
                    <ToggleButtonGroup
                        value={selectedPreset}
                        exclusive
                        onChange={(_, v) => {
                            if (v) dispatch(applyCardPreset(v));
                        }}
                        size="small"
                        fullWidth
                    >
                        {PRESET_OPTIONS.map(({ value, icon, labelKey }) => (
                            <Tooltip key={value} title={t(labelKey)}>
                                <ToggleButton value={value}>
                                    {icon}
                                </ToggleButton>
                            </Tooltip>
                        ))}
                    </ToggleButtonGroup>
                </SettingRow>

                <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ display: "block", px: 2, pt: 0.5 }}
                >
                    {t("sideMenu.customization.elements")}
                </Typography>
                <List dense disablePadding>
                    {displayToggles.map(({ label, checked, action }, index) => (
                        <Fragment key={label}>
                            {index === THUMBNAIL_ROW_INDEX && (
                                <>
                                    {/* A width rather than a switch: how much of a card a
                        picture should take depends on the pictures, and the
                        reader is the one looking at them. Nought is off, which is
                        what makes this the thumbnail element's switch as well. */}
                                    <ListItem
                                        secondaryAction={
                                            <Slider
                                                value={thumbnailWidthRem}
                                                onChange={(_, v) =>
                                                    dispatch(
                                                        setThumbnailWidthRem(
                                                            v as number,
                                                        ),
                                                    )
                                                }
                                                min={0}
                                                max={THUMBNAIL_WIDTH_MAX_REM}
                                                step={THUMBNAIL_WIDTH_STEP_REM}
                                                size="small"
                                                valueLabelDisplay="auto"
                                                valueLabelFormat={(v) =>
                                                    v === 0
                                                        ? t(
                                                              "sideMenu.customization.thumbnailNone",
                                                          )
                                                        : `${v}`
                                                }
                                                aria-label={t(
                                                    "sideMenu.fields.thumbnails",
                                                )}
                                                sx={THUMBNAIL_SLIDER_SX}
                                            />
                                        }
                                    >
                                        <ListItemText
                                            primary={t(
                                                "sideMenu.fields.thumbnails",
                                            )}
                                        />
                                    </ListItem>
                                </>
                            )}
                            <ListItem
                                secondaryAction={
                                    <Switch
                                        edge="end"
                                        size="small"
                                        checked={checked}
                                        onChange={(e) =>
                                            action(e.target.checked)
                                        }
                                    />
                                }
                            >
                                <ListItemText primary={label} />
                            </ListItem>
                        </Fragment>
                    ))}
                </List>
            </Box>

            <Divider />

            {/* ── Section 2: Card Fields ───────────────────────── */}
            <Box data-tour="customization-card-fields">
                <Typography
                    variant="subtitle2"
                    sx={{ px: 2, pt: 1.5, pb: 0.5 }}
                >
                    {t("sideMenu.customization.cardFields")}
                </Typography>
                <ToggleButtonGroup
                    value={fieldLayout}
                    exclusive
                    onChange={(_, v) => {
                        if (v) dispatch(setFieldLayout(v));
                    }}
                    size="small"
                    fullWidth
                    sx={{ px: 1, pb: 0.5 }}
                >
                    {FIELD_LAYOUT_OPTIONS.map(({ value, icon, labelKey }) => (
                        <Tooltip key={value} title={t(labelKey)}>
                            <ToggleButton value={value}>{icon}</ToggleButton>
                        </Tooltip>
                    ))}
                </ToggleButtonGroup>
                {/* Field names and columns are drawn by the compact layout
                and by nothing else: the line layout keeps its names in the
                column header above the list and is already one column per
                field. Offering the controls there would be offering settings
                that do nothing. */}
                {fieldLayout === "compact" && (
                    <Box sx={FIELD_SETTING_ROW_SX}>
                        <Typography variant="caption" color="text.secondary">
                            {t("sideMenu.fields.fieldNames")}
                        </Typography>
                        <Switch
                            size="small"
                            checked={showFieldNames}
                            onChange={(e) =>
                                dispatch(setShowFieldNames(e.target.checked))
                            }
                        />
                    </Box>
                )}
                {fieldLayout === "compact" &&
                    Array.from({ length: columnCount }, (_, column) => (
                        <Box
                            key={column}
                            data-field-zone={column}
                            {...zoneProps(column)}
                            sx={FIELD_ZONE_SX}
                        >
                            <Typography
                                variant="caption"
                                color="text.secondary"
                                sx={FIELD_ZONE_LABEL_SX}
                            >
                                {t("sideMenu.customization.fieldColumn", {
                                    number: column + 1,
                                })}
                            </Typography>
                            {fieldsIn(column).map((field) =>
                                renderChip(field, column),
                            )}
                        </Box>
                    ))}
                {fieldLayout !== "compact" && (
                    <Box sx={FIELD_LIST_SX}>
                        {selectedFields.map((field) => renderChip(field))}
                    </Box>
                )}
                <Box sx={FIELD_ADD_ROW_SX}>
                    {fieldLayout === "compact" && (
                        <>
                            <Tooltip
                                title={t("sideMenu.customization.removeColumn")}
                            >
                                <span>
                                    <IconButton
                                        size="small"
                                        onClick={() =>
                                            dispatch(removeFieldColumn())
                                        }
                                        disabled={columnCount <= 1}
                                    >
                                        <Remove fontSize="small" />
                                    </IconButton>
                                </span>
                            </Tooltip>
                            <Tooltip
                                title={t("sideMenu.customization.addColumn")}
                            >
                                <span>
                                    <IconButton
                                        size="small"
                                        onClick={() =>
                                            dispatch(addFieldColumn())
                                        }
                                        disabled={
                                            columnCount >= MAX_FIELD_COLUMNS
                                        }
                                    >
                                        <ViewColumnOutlined fontSize="small" />
                                    </IconButton>
                                </span>
                            </Tooltip>
                            <Box sx={FIELD_ADD_SPACER_SX} />
                        </>
                    )}
                    <Tooltip title={t("sideMenu.customization.addField")}>
                        <span>
                            <IconButton
                                size="small"
                                onClick={(e) => setAddAnchorEl(e.currentTarget)}
                                disabled={unselectedFields.length === 0}
                            >
                                <Add fontSize="small" />
                            </IconButton>
                        </span>
                    </Tooltip>
                    <Menu
                        anchorEl={addAnchorEl}
                        open={Boolean(addAnchorEl)}
                        onClose={() => setAddAnchorEl(null)}
                    >
                        {unselectedFields.map((field) => (
                            <MenuItem
                                key={field.id}
                                dense
                                onClick={() => {
                                    handlePreviewFieldToggle(field.id);
                                    setAddAnchorEl(null);
                                }}
                            >
                                {field.label}
                            </MenuItem>
                        ))}
                    </Menu>
                </Box>
            </Box>
        </>
    );
};
