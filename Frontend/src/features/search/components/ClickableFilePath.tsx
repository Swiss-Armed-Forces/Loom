import { useAppDispatch, useAppSelector } from "../../../app/hooks";
import { updateFilenameOfQuery } from "../SearchQueryUtils";
import { selectQuery, updateQuery } from "../searchSlice";
import { Breadcrumbs, Link } from "@mui/material";

interface ClickableFilePathProps {
    fullPath: string;
}

export function ClickableFilePath({ fullPath }: ClickableFilePathProps) {
    const searchQuery = useAppSelector(selectQuery);
    const dispatch = useAppDispatch();

    const fullPathParts = fullPath.split("/").filter((part) => part !== "");
    const fullPathPartsExtended = fullPathParts.map((part, idx) => {
        return {
            part: part,
            pathToPart: `//${fullPathParts
                .filter((_, innerIdx) => innerIdx <= idx)
                .join("/")}`,
        };
    });

    const handleQueryReplaceFilename = (newFilepath: string) => {
        const newQuery = updateFilenameOfQuery(
            searchQuery?.query ?? "",
            newFilepath,
        );
        dispatch(
            updateQuery({
                query: newQuery,
            }),
        );
    };

    return (
        <Breadcrumbs
            separator="/"
            sx={{
                "& .MuiBreadcrumbs-separator": { mx: 0.25 },
            }}
            maxItems={4}
            itemsBeforeCollapse={0}
            itemsAfterCollapse={3}
        >
            {fullPathPartsExtended.map((part, idx) => (
                <Link
                    key={idx}
                    color="inherit"
                    onClick={() => handleQueryReplaceFilename(part.pathToPart)}
                    sx={{
                        cursor: "pointer",
                        textDecoration: "none",
                        "&:hover": {
                            textDecoration: "underline",
                            color: "secondary.main",
                        },
                    }}
                >
                    {part.part}
                </Link>
            ))}
        </Breadcrumbs>
    );
}
