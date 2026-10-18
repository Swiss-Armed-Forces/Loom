import {
    Add,
    AutoModeOutlined,
    DensityLarge,
    DensityMedium,
    DensitySmall,
    ViewAgendaOutlined,
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
    MenuItem,
    Switch,
    ToggleButton,
    ToggleButtonGroup,
    Tooltip,
    Typography,
} from "@mui/material";
import { ReactNode, useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { getPreviewFields } from "@app/api";
import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    CardDensity,
    FieldLayout,
    NamedDensity,
    applyDensityPreset,
    selectAvailablePreviewFields,
    selectCardDensity,
    selectCardElementVisibility,
    selectFieldLayout,
    selectMatchingDensityPreset,
    selectPreviewFields,
    selectResolvedCardDensity,
    setAvailablePreviewFields,
    setCardDensity,
    setFieldLayout,
    setPreviewFields,
    setShowActions,
    setShowAttachments,
    setShowExtensionIcon,
    setShowFieldActions,
    setShowFieldSections,
    setShowFilePath,
    setShowHighlights,
    setShowParentNavigation,
    setShowSortIndicator,
    setShowStatusIndicators,
    setShowTags,
    setShowThumbnails,
} from "@app/slices/searchSlice";
import { useFieldReorder } from "@features/search/hooks/useFieldReorder";

/** The spacings, in the order they read: tightest first. */
const SPACING_OPTIONS: {
    value: NamedDensity;
    icon: React.ReactNode;
    labelKey: string;
}[] = [
    {
        value: "compact",
        icon: <DensitySmall />,
        labelKey: "toolbar.cardDensity.compact",
    },
    {
        value: "standard",
        icon: <DensityMedium />,
        labelKey: "toolbar.cardDensity.standard",
    },
    {
        value: "full",
        icon: <DensityLarge />,
        labelKey: "toolbar.cardDensity.full",
    },
];

/** A preset is a shortcut to a whole look - a spacing *and* a set of
 *  elements - so it offers the same names plus "auto", which hands the
 *  spacing back to the window. */
const PRESET_OPTIONS: {
    value: CardDensity;
    icon: React.ReactNode;
    labelKey: string;
}[] = [
    {
        value: "auto",
        icon: <AutoModeOutlined />,
        labelKey: "toolbar.cardDensity.auto",
    },
    ...SPACING_OPTIONS,
];

const FIELD_LAYOUT_OPTIONS: {
    value: FieldLayout;
    icon: React.ReactNode;
    labelKey: string;
}[] = [
    {
        value: "rows",
        icon: <ViewAgendaOutlined />,
        labelKey: "sideMenu.customization.fieldLayoutRows",
    },
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
 *  names, so the two toggle groups do not read as one five-button row. */
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
    const cardDensity = useAppSelector(selectCardDensity);
    const resolvedDensity = useAppSelector(selectResolvedCardDensity);
    const matchingPreset = useAppSelector(selectMatchingDensityPreset);
    // "auto" is a preset of its own: it is the one that leaves the spacing to
    // the window. It only counts as the current preset while the switches
    // still read as the preset the window resolved to.
    const selectedPreset =
        matchingPreset === null
            ? null
            : cardDensity === "auto"
              ? "auto"
              : matchingPreset;
    const fieldLayout = useAppSelector(selectFieldLayout);
    const vis = useAppSelector(selectCardElementVisibility);
    const [error, setError] = useState<string | null>(null);
    const [addAnchorEl, setAddAnchorEl] = useState<HTMLElement | null>(null);
    const { dragProps, isDragging, isDropTarget } = useFieldReorder();

    const fetchFields = useCallback(async () => {
        try {
            const fields = await getPreviewFields();
            dispatch(setAvailablePreviewFields(fields));
            setError(null);
        } catch (err) {
            setError(String(err));
        }
    }, [dispatch]);

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
    const unselectedFields = availableFields.filter(
        (f) => !previewFields.includes(f.id),
    );

    const displayToggles: {
        label: string;
        checked: boolean;
        action: (v: boolean) => void;
    }[] = [
        {
            label: t("sideMenu.fields.thumbnails"),
            checked: vis.showThumbnails,
            action: (v) => dispatch(setShowThumbnails(v)),
        },
        {
            label: t("sideMenu.fields.highlights"),
            checked: vis.showHighlights,
            action: (v) => dispatch(setShowHighlights(v)),
        },
        {
            label: t("sideMenu.fields.fieldSections"),
            checked: vis.showFieldSections,
            action: (v) => dispatch(setShowFieldSections(v)),
        },
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

                {/* A preset sets both rows below at once. Nothing is selected
                here once the switches have been taken somewhere no preset
                describes - the row reports what the card reads as rather than
                holding a mode of its own. */}
                <SettingRow label={t("sideMenu.customization.preset")}>
                    <ToggleButtonGroup
                        value={selectedPreset}
                        exclusive
                        onChange={(_, v) => {
                            if (v) dispatch(applyDensityPreset(v));
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

                {/* Spacing alone: the room a card takes, leaving every switch
                below exactly as it is. While the preset is "auto" this shows
                the spacing the width resolved to, and picking one pins it. */}
                <SettingRow label={t("sideMenu.customization.spacing")}>
                    <ToggleButtonGroup
                        value={resolvedDensity}
                        exclusive
                        onChange={(_, v) => {
                            if (v) dispatch(setCardDensity(v));
                        }}
                        size="small"
                        fullWidth
                    >
                        {SPACING_OPTIONS.map(({ value, icon, labelKey }) => (
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
                    {displayToggles.map(({ label, checked, action }) => (
                        <ListItem
                            key={label}
                            secondaryAction={
                                <Switch
                                    edge="end"
                                    size="small"
                                    checked={checked}
                                    onChange={(e) => action(e.target.checked)}
                                />
                            }
                        >
                            <ListItemText primary={label} />
                        </ListItem>
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
                <Box
                    sx={{
                        px: 1.5,
                        py: 1,
                        display: "flex",
                        flexWrap: "wrap",
                        gap: 0.5,
                        alignItems: "center",
                    }}
                >
                    {selectedFields.map((field, index) => (
                        <Tooltip
                            key={field.id}
                            title={t("sideMenu.customization.dragToOrder")}
                        >
                            <Chip
                                label={field.label}
                                size="small"
                                onDelete={() =>
                                    handlePreviewFieldToggle(field.id)
                                }
                                {...dragProps(index)}
                                sx={{
                                    cursor: "grab",
                                    opacity: isDragging(index) ? 0.4 : 1,
                                    boxShadow: isDropTarget(index)
                                        ? (theme) =>
                                              `inset 2px 0 0 ${theme.palette.primary.main}`
                                        : undefined,
                                }}
                            />
                        </Tooltip>
                    ))}
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
