import { ArchiveContent } from "../../../app/api";
import { formatFileSize } from "../../search/util";
import { HighlightedSpan } from "./HighlightedSpan";

interface FileSizeLabelProps {
    searchQuery: string;
    content: ArchiveContent;
}

export function FileSizeLabel({ searchQuery, content }: FileSizeLabelProps) {
    const SIZE_QUERY = /((^|\s)size(>|<)[=]{0,1})([0-9]*)([k|m]{0,1})/im;

    const size = content.size;
    const sizeHighlighted = size ? SIZE_QUERY.test(searchQuery) : false;

    return (
        <HighlightedSpan isHighlighted={sizeHighlighted}>
            {formatFileSize(size)}
        </HighlightedSpan>
    );
}
