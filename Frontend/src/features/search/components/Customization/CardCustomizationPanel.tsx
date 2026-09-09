import {
    Add,
    AutoModeOutlined,
    Check,
    Close,
    DensityLarge,
    DensityMedium,
    DensitySmall,
    FlagOutlined,
    ImageSearch,
    MarkEmailUnreadOutlined,
    SummarizeOutlined,
    Translate,
    TuneOutlined,
    YoutubeSearchedForOutlined,
} from "@mui/icons-material";
import {
    Box,
    Chip,
    Divider,
    IconButton,
    List,
    ListItem,
    ListItemButton,
    ListItemIcon,
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
    AutoActionsPreferences,
    CardDensity,
    selectAutoActionsPreferences,
    selectAvailablePreviewFields,
    selectCardDensity,
    selectCardElementVisibility,
    selectPreviewFields,
    setAutoActionPreference,
    setAvailablePreviewFields,
    setCardDensity,
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

const DENSITY_OPTIONS: {
    value: CardDensity;
    icon: React.ReactNode;
    labelKey: string;
}[] = [
    {
        value: "auto",
        icon: <AutoModeOutlined />,
        labelKey: "toolbar.cardDensity.auto",
    },
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
    {
        value: "custom",
        icon: <TuneOutlined />,
        labelKey: "toolbar.cardDensity.custom",
    },
];

export const CardCustomizationPanel = () => {
    const dispatch = useAppDispatch();
    const { t } = useTranslation();
    const availableFields = useAppSelector(selectAvailablePreviewFields);
    const previewFields = useAppSelector(selectPreviewFields);
    const cardDensity = useAppSelector(selectCardDensity);
    const vis = useAppSelector(selectCardElementVisibility);
    const autoActionsPrefs = useAppSelector(selectAutoActionsPreferences);
    const [error, setError] = useState<string | null>(null);
    const [addAnchorEl, setAddAnchorEl] = useState<HTMLElement | null>(null);

    const autoActionRow = (
        key: keyof AutoActionsPreferences,
        icon: ReactNode,
        label: string,
    ) => {
        const enabled = autoActionsPrefs[key];
        return (
            <ListItemButton
                key={key}
                onClick={() =>
                    dispatch(setAutoActionPreference({ key, value: !enabled }))
                }
                dense
            >
                <ListItemIcon sx={{ minWidth: 36 }}>{icon}</ListItemIcon>
                <ListItemText primary={label} />
                {enabled ? (
                    <Check sx={{ fontSize: 16, color: "success.main" }} />
                ) : (
                    <Close
                        sx={{ fontSize: 16, color: "error.main", opacity: 0.5 }}
                    />
                )}
            </ListItemButton>
        );
    };

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

    const selectedFields = availableFields.filter((f) =>
        previewFields.includes(f.id),
    );
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
            <Box data-tour="card-customization-display">
                <Typography
                    variant="subtitle2"
                    sx={{ px: 2, pt: 1.5, pb: 0.5 }}
                >
                    {t("sideMenu.cardCustomization.cardDisplay")}
                </Typography>
                <ToggleButtonGroup
                    value={cardDensity}
                    exclusive
                    onChange={(_, v) => {
                        if (v) dispatch(setCardDensity(v));
                    }}
                    size="small"
                    fullWidth
                    sx={{ px: 1, pb: 0.5 }}
                >
                    {DENSITY_OPTIONS.map(({ value, icon, labelKey }) => (
                        <Tooltip key={value} title={t(labelKey)}>
                            <ToggleButton value={value}>{icon}</ToggleButton>
                        </Tooltip>
                    ))}
                </ToggleButtonGroup>
                {cardDensity === "custom" && (
                    <List dense disablePadding>
                        {displayToggles.map(({ label, checked, action }) => (
                            <ListItem
                                key={label}
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
                        ))}
                    </List>
                )}
            </Box>

            <Divider />

            {/* ── Section 2: Card Fields ───────────────────────── */}
            <Box data-tour="card-customization-fields">
                <Typography
                    variant="subtitle2"
                    sx={{ px: 2, pt: 1.5, pb: 0.5 }}
                >
                    {t("sideMenu.cardCustomization.cardFields")}
                </Typography>
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
                    {selectedFields.map((field) => (
                        <Chip
                            key={field.id}
                            label={field.label}
                            size="small"
                            onDelete={() => handlePreviewFieldToggle(field.id)}
                        />
                    ))}
                    <Tooltip title={t("sideMenu.cardCustomization.addField")}>
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

            <Divider />

            {/* ── Section 3: Auto Actions ──────────────────────── */}
            <Box data-tour="card-customization-auto-actions">
                <Typography
                    variant="subtitle2"
                    sx={{ px: 2, pt: 1.5, pb: 0.5 }}
                >
                    {t("sideMenu.cardCustomization.autoActions")}
                </Typography>
                <List dense disablePadding>
                    {autoActionRow(
                        "flag",
                        <FlagOutlined />,
                        t("sideMenu.autoActions.flag"),
                    )}
                    {autoActionRow(
                        "markAsSeen",
                        <MarkEmailUnreadOutlined />,
                        t("sideMenu.autoActions.markAsSeen"),
                    )}
                    {autoActionRow(
                        "translate",
                        <Translate />,
                        t("sideMenu.autoActions.translate"),
                    )}
                    {autoActionRow(
                        "summarize",
                        <SummarizeOutlined />,
                        t("sideMenu.autoActions.summarize"),
                    )}
                    {autoActionRow(
                        "describeImage",
                        <ImageSearch />,
                        t("sideMenu.autoActions.describeImage"),
                    )}
                    {autoActionRow(
                        "reindex",
                        <YoutubeSearchedForOutlined />,
                        t("sideMenu.autoActions.reindex"),
                    )}
                </List>
            </Box>
        </>
    );
};
