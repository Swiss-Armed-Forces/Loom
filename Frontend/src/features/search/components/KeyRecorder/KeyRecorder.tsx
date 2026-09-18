import { Edit as EditIcon, Close as CloseIcon } from "@mui/icons-material";
import { Box, Typography, IconButton } from "@mui/material";
import { useState, useCallback, useEffect, useRef } from "react";
import React from "react";
import { useTranslation } from "react-i18next";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    setBinding,
    resetBinding,
    selectResolvedBindings,
} from "@app/slices/searchSlice";
import { formatKey } from "@features/search/hooks/shortcutRegistry";

import styles from "./KeyRecorder.module.css";

interface KeyRecorderProps {
    actionId: string;
    currentKeys: string[];
    defaultKeys?: string[];
    compact?: boolean;
    readOnly?: boolean;
}

export const KeyRecorder: React.FC<KeyRecorderProps> = ({
    actionId,
    currentKeys,
    defaultKeys = [],
    compact = false,
    readOnly = false,
}) => {
    const dispatch = useAppDispatch();
    const resolvedBindings = useAppSelector(selectResolvedBindings);
    const { t } = useTranslation();
    const [isRecording, setIsRecording] = useState(false);
    const [tempKeys, setTempKeys] = useState<string[]>([]);
    const containerRef = useRef<HTMLDivElement>(null);

    // Reset temp keys when not recording
    useEffect(() => {
        if (!isRecording) {
            setTempKeys([]);
        }
    }, [isRecording]);

    // Handle escape to cancel recording (document-level for global escape)
    useEffect(() => {
        if (!isRecording) return;

        const handleEscape = (event: KeyboardEvent) => {
            if (event.key === "Escape") {
                event.preventDefault();
                setIsRecording(false);
                setTempKeys([]);
            }
        };

        document.addEventListener("keydown", handleEscape);
        return () => document.removeEventListener("keydown", handleEscape);
    }, [isRecording]);

    // Commit binding
    const commitBinding = useCallback(
        (keys: string[]) => {
            // Check for conflicts before committing
            const tempCombo = keys.join(" + ");
            const hasConflict = Object.entries(resolvedBindings).some(
                ([otherActionId, otherKeys]) => {
                    if (otherActionId === actionId) return false;
                    return otherKeys.some(
                        (combo) =>
                            combo.toLowerCase() === tempCombo.toLowerCase(),
                    );
                },
            );

            // Don't save if there's a conflict
            if (hasConflict) {
                setIsRecording(false);
                setTempKeys([]);
                return;
            }

            if (keys.length > 0) {
                dispatch(setBinding({ actionId, keys }));
            } else {
                // Reset to default if empty
                dispatch(resetBinding(actionId));
            }
            setIsRecording(false);
        },
        [actionId, dispatch, resolvedBindings],
    );

    // Handle key recording on the container
    const handleContainerKeyDown = useCallback(
        (event: React.KeyboardEvent<HTMLDivElement>) => {
            if (!isRecording) return;

            // Prevent default for most keys but allow some
            const allowedKeys = ["Escape", "Tab"];
            if (!allowedKeys.includes(event.key)) {
                event.preventDefault();
                event.stopPropagation();
            }

            // Escape cancels (also handled by document listener)
            if (event.key === "Escape") {
                setIsRecording(false);
                setTempKeys([]);
                return;
            }

            // Tab moves focus - commit first
            if (event.key === "Tab") {
                if (tempKeys.length > 0) {
                    commitBinding(tempKeys);
                } else {
                    setIsRecording(false);
                }
                return;
            }

            // Enter commits
            if (event.key === "Enter") {
                if (tempKeys.length > 0) {
                    commitBinding(tempKeys);
                }
                return;
            }

            // Backspace/Delete clears
            if (event.key === "Backspace" || event.key === "Delete") {
                setTempKeys([]);
                return;
            }

            // Build the key combination
            const newKeys: string[] = [];
            if (event.ctrlKey) newKeys.push("Ctrl");
            if (event.shiftKey) newKeys.push("Shift");
            if (event.altKey) newKeys.push("Alt");
            if (event.metaKey) newKeys.push("Meta");

            // Add the main key (convert to lowercase for letter keys)
            const mainKey = event.key;
            if (
                mainKey !== "Shift" &&
                mainKey !== "Ctrl" &&
                mainKey !== "Alt" &&
                mainKey !== "Meta" &&
                mainKey !== "Escape" &&
                mainKey !== "Backspace" &&
                mainKey !== "Delete" &&
                mainKey !== "Tab"
            ) {
                // Convert single letter keys to lowercase and remove Shift if present
                if (mainKey.length === 1 && mainKey >= "A" && mainKey <= "Z") {
                    newKeys.push(mainKey.toLowerCase());
                } else {
                    newKeys.push(mainKey);
                }
            }

            if (newKeys.length > 0) {
                setTempKeys(newKeys);
            }
        },
        [isRecording, tempKeys, commitBinding],
    );

    const handleClick = useCallback(() => {
        if (isRecording || readOnly) return;
        setIsRecording(true);
        containerRef.current?.focus();
    }, [isRecording, readOnly]);

    // Handle blur - only commit if we have temp keys
    const handleBlur = useCallback(() => {
        if (!isRecording) return;
        // Only commit if we have temp keys, otherwise just exit recording mode
        if (tempKeys.length > 0) {
            commitBinding(tempKeys);
        } else {
            setIsRecording(false);
        }
    }, [isRecording, tempKeys, commitBinding]);

    // Cancel button handler
    const handleCancel = useCallback((event: React.MouseEvent) => {
        event.stopPropagation();
        event.preventDefault();
        setIsRecording(false);
        setTempKeys([]);
    }, []);

    // Reset to default handler
    const handleReset = useCallback(
        (event: React.MouseEvent) => {
            event.stopPropagation();
            dispatch(resetBinding(actionId));
        },
        [actionId, dispatch],
    );

    // Display the current/recorded keys
    const displayKeys = isRecording ? tempKeys : currentKeys;

    const isModified =
        currentKeys.length > 0 &&
        (defaultKeys.length === 0 ||
            JSON.stringify(currentKeys) !== JSON.stringify(defaultKeys));

    const hasConflict =
        isRecording &&
        tempKeys.length > 0 &&
        (() => {
            const tempCombo = tempKeys.join(" + ");
            const conflict = Object.entries(resolvedBindings).some(
                ([otherActionId, otherKeys]) => {
                    if (otherActionId === actionId) return false;
                    return otherKeys.some(
                        (combo) =>
                            combo.toLowerCase() === tempCombo.toLowerCase(),
                    );
                },
            );
            return conflict;
        })();

    // Helper to render keys with formatKey applied
    const renderKeyChips = (keys: string[]) => {
        return keys.map((key, index) => (
            <React.Fragment key={index}>
                <Box className={styles.keyChip}>
                    <kbd>{formatKey(key)}</kbd>
                </Box>
                {index < keys.length - 1 && (
                    <span className={styles.separator}>/</span>
                )}
            </React.Fragment>
        ));
    };

    return (
        <Box
            ref={containerRef}
            className={`${styles.container} ${
                isRecording ? styles.recording : ""
            } ${compact ? styles.compact : ""} ${
                readOnly ? styles.readOnly : ""
            }`}
            onClick={handleClick}
            onKeyDown={handleContainerKeyDown}
            onBlur={handleBlur}
            tabIndex={readOnly ? -1 : 0}
            role="button"
            aria-label={`Shortcut for ${actionId}${readOnly ? " (read-only)" : ""}`}
            aria-pressed={isRecording}
            align-items="center"
        >
            {isRecording ? (
                // Recording state
                <Box onClick={(e) => e.stopPropagation()}>
                    <kbd>
                        <Box className={styles.keyChip} sx={{ margin: "0px" }}>
                            <Typography
                                variant="body2"
                                sx={{
                                    color: hasConflict ? "#f44336" : "inherit",
                                }}
                            >
                                {displayKeys.length > 0
                                    ? displayKeys.map((key, idx) => (
                                          <React.Fragment key={idx}>
                                              {formatKey(key)}
                                              {idx < displayKeys.length - 1 && (
                                                  <span> + </span>
                                              )}
                                          </React.Fragment>
                                      ))
                                    : t("sideMenu.customizations.pressKey")}
                            </Typography>
                        </Box>

                        <IconButton
                            size="small"
                            onMouseDown={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                            }}
                            onClick={handleCancel}
                            className={styles.cancelButton}
                            aria-label={t("common.cancel")}
                        >
                            <CloseIcon fontSize="small" />
                        </IconButton>
                    </kbd>
                    <Box>
                        {hasConflict && (
                            <Typography
                                variant="caption"
                                sx={{
                                    color: "#f44336",
                                    display: "block",
                                    marginTop: "2px",
                                }}
                            >
                                {t("sideMenu.customizations.alreadyUsed")}
                            </Typography>
                        )}
                    </Box>
                </Box>
            ) : (
                // Normal state
                <Box className={styles.normalState}>
                    <Box className={styles.keysContainer}>
                        {displayKeys.length > 0 ? (
                            renderKeyChips(displayKeys)
                        ) : (
                            <Typography
                                variant="body2"
                                className={styles.notSetText}
                            >
                                {t("sideMenu.customizations.notSet")}
                            </Typography>
                        )}
                    </Box>
                    {!compact && !readOnly && (
                        <>
                            <EditIcon
                                className={styles.editIcon}
                                fontSize="small"
                            />
                            {isModified && (
                                <IconButton
                                    size="small"
                                    onClick={handleReset}
                                    className={styles.resetButton}
                                    aria-label={t(
                                        "sideMenu.customizations.resetDefault",
                                    )}
                                    title={t(
                                        "sideMenu.customizations.resetDefault",
                                    )}
                                >
                                    <CloseIcon fontSize="small" />
                                </IconButton>
                            )}
                        </>
                    )}
                </Box>
            )}
        </Box>
    );
};

export default KeyRecorder;
