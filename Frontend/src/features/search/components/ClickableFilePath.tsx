import { useAppDispatch, useAppSelector } from "../../../app/hooks";
import { updateFilenameOfQuery } from "../SearchQueryUtils";
import { selectQuery, updateQuery } from "../searchSlice";
import styles from "./ClickableFilePath.module.css";

interface ClickableFilePathProps {
    fullPath: string;
}

export function ClickableFilePath({ fullPath }: ClickableFilePathProps) {
    const searchQuery = useAppSelector(selectQuery);
    const dispatch = useAppDispatch();

    const fullPathParts = fullPath.split("/").filter((part) => part !== "");
    const fullPathPartsExtended = fullPathParts.map((part, idx) => {
        const isLast = idx === fullPathParts.length - 1;
        const trailingSymbol = isLast ? "" : "/";

        return {
            part: `${part}${trailingSymbol}`,
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
        <div>
            <div className={styles.metaFullNameLineContainer}>
                <span>&#47;&#47;</span>
                {fullPathPartsExtended.map((part, idx) => (
                    <span
                        className={styles.metaFullNamePart}
                        key={idx}
                        onClick={() =>
                            handleQueryReplaceFilename(part.pathToPart)
                        }
                    >
                        {part.part}
                    </span>
                ))}
            </div>
        </div>
    );
}
