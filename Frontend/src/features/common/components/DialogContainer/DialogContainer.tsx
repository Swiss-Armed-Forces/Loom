import React, { useCallback } from "react";

import { useAppDispatch, useAppSelector } from "@app/hooks";
import {
    DialogProps,
    closeDialog,
    selectDialogs,
} from "@app/slices/commonSlice";
import { DialogType } from "@features/common/utils/enums";

import {
    AboutDialog,
    AddTagsDialog,
    CreateArchiveDialog,
    DeleteCustomQueryDialog,
    DeleteTagGloballyDialog,
    EncryptionKeyInfoDialog,
    FileDetailDialog,
    ImageDescriptionDialog,
    SummaryDialog,
    TranslationDialog,
    UploadFileDialog,
} from "./Dialogs";

// Validates at registration time that a dialog component accepts DialogProps
// (including isTop). The return type is kept as any so the heterogeneous
// registry remains flexible at read time.
const registerDialog = <P extends DialogProps>(
    c: React.ComponentType<P>,
): React.ComponentType<any> => c;

const dialogRegistry: Record<DialogType, React.ComponentType<any>> = {
    [DialogType.About]: registerDialog(AboutDialog),
    [DialogType.EncryptionKeyInfo]: registerDialog(EncryptionKeyInfoDialog),
    [DialogType.AddTagsDialog]: registerDialog(AddTagsDialog),
    [DialogType.CreateArchive]: registerDialog(CreateArchiveDialog),
    [DialogType.DeleteCustomQuery]: registerDialog(DeleteCustomQueryDialog),
    [DialogType.DeleteTagGlobally]: registerDialog(DeleteTagGloballyDialog),
    [DialogType.FileDetail]: registerDialog(FileDetailDialog),
    [DialogType.ImageDescription]: registerDialog(ImageDescriptionDialog),
    [DialogType.Summary]: registerDialog(SummaryDialog),
    [DialogType.Translation]: registerDialog(TranslationDialog),
    [DialogType.UploadFile]: registerDialog(UploadFileDialog),
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
    const topDialogId =
        dialogs.length > 0 ? dialogs[dialogs.length - 1].id : null;

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
                        isTop={dialog.id === topDialogId}
                        onClose={() => handleClose(dialog.id)}
                    />
                );
            })}
        </>
    );
};
