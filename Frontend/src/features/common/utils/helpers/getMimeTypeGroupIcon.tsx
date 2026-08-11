import {
    Article,
    AttachFile,
    Audiotrack,
    Description,
    Email,
    Image,
    InsertDriveFile,
    TextFields,
    Vibration,
    Videocam,
    ViewInAr,
} from "@mui/icons-material";
import { ReactElement } from "react";

export const getMimeTypeGroupIcon = (
    group: string | null | undefined,
): ReactElement => {
    switch (group) {
        case "image":
            return <Image />;
        case "video":
            return <Videocam />;
        case "audio":
            return <Audiotrack />;
        case "text":
            return <Article />;
        case "message":
            return <Email />;
        case "multipart":
            return <AttachFile />;
        case "font":
            return <TextFields />;
        case "haptics":
            return <Vibration />;
        case "model":
            return <ViewInAr />;
        case "application":
            return <Description />;
        default:
            return <InsertDriveFile />;
    }
};
