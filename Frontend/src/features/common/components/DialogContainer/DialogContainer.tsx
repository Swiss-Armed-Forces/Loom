import React, { useCallback } from "react";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import { closeDialog, selectDialogs } from "@app/slices/commonSlice";
import { DialogType } from "@features/common/utils/enums";

import {
    AboutDialog,
    AddTagsDialog,
    CreateArchiveDialog,
    DeleteCustomQueryDialog,
    DeleteTagGloballyDialog,
    FileDetailDialog,
    SummaryDialog,
    TranslationDialog,
    UploadFileDialog,
} from "./Dialogs";

const dialogRegistry: Record<DialogType, React.ComponentType<any>> = {
    [DialogType.About]: AboutDialog,
    [DialogType.AddTagsDialog]: AddTagsDialog,
    [DialogType.CreateArchive]: CreateArchiveDialog,
    [DialogType.DeleteCustomQuery]: DeleteCustomQueryDialog,
    [DialogType.DeleteTagGlobally]: DeleteTagGloballyDialog,
    [DialogType.FileDetail]: FileDetailDialog,
    [DialogType.Summary]: SummaryDialog,
    [DialogType.Translation]: TranslationDialog,
    [DialogType.UploadFile]: UploadFileDialog,
};

export const DialogContainer = () => {
    const dialogs = useAppSelector(selectDialogs);
    const dispatch = useAppDispatch();

    const handleClose = useCallback(
        (id: string) => {
            dispatch(closeDialog(id));
        },
        [dispatch],
    );
    return (
        <>
            {dialogs.map((dialog) => {
                const Component = dialogRegistry[dialog.type];
                if (!Component) return null;

                return (
                    <Component
                        key={dialog.id}
                        id={dialog.id}
                        {...dialog.props}
                        onClose={() => handleClose(dialog.id)}
                    />
                );
            })}
        </>
    );
};
