import Avatar from "@mui/material/Avatar";
import { Badge } from "@mui/material";
import { AttachFile, ContentCut } from "@mui/icons-material";
import { ReactNode } from "react";

interface FileAvatarProps {
    hasAttachments: boolean;
    isTruncated: boolean;
    fileExtension: string;
    performSearch: (query: string) => void;
}

interface BaseFileAvatarProps {
    children: ReactNode;
}

const getHashCode = (str: string): number => {
    let hash = 0;

    if (str.length === 0) {
        return hash;
    }

    for (let i = 0; i < str.length; i++) {
        const char = str.charCodeAt(i);
        hash = (hash << 5) - hash + char;
        hash = hash & hash; // Convert to 32bit integer
    }

    return hash;
};

export function FileAvatar({
    hasAttachments,
    isTruncated,
    fileExtension,
    performSearch,
}: FileAvatarProps) {
    const colors = [
        "#EF5350",
        "#E53935",
        "#D81B60",
        "#EC407A",
        "#AB47BC",
        "#7E57C2",
        "#5C6BC0",
        "#2196F3",
        "#43A047",
        "#EF6C00",
        "#A1887F",
        "#78909C",
        "#FF4081",
        "#3949AB",
    ];

    const BaseFileAvatar = ({ children }: BaseFileAvatarProps) => {
        if (isTruncated && hasAttachments) {
            return (
                <Badge badgeContent={<AttachFile />}>
                    <Badge
                        badgeContent={<ContentCut />}
                        anchorOrigin={{
                            vertical: "top",
                            horizontal: "left",
                        }}
                    >
                        {children}
                    </Badge>
                </Badge>
            );
        } else if (hasAttachments) {
            return <Badge badgeContent={<AttachFile />}>{children}</Badge>;
        } else if (isTruncated) {
            return (
                <Badge
                    badgeContent={<ContentCut />}
                    anchorOrigin={{
                        vertical: "top",
                        horizontal: "left",
                    }}
                >
                    {children}
                </Badge>
            );
        } else {
            return <>{children}</>;
        }
    };

    return (
        <BaseFileAvatar>
            <Avatar
                onClick={() => performSearch(`*.${fileExtension}`)}
                style={{
                    fontSize: "12px",
                    textTransform: "uppercase",
                    cursor: "pointer",
                    backgroundColor:
                        colors[getHashCode(fileExtension) % colors.length],
                }}
            >
                {fileExtension}
            </Avatar>
        </BaseFileAvatar>
    );
}
