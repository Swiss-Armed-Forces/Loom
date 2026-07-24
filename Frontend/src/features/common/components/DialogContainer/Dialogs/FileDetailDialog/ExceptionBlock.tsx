import { ExpandableTextBlock } from "./ExpandableTextBlock";

interface ExceptionBlockProps {
    text: string;
}

export const ExceptionBlock = ({ text }: ExceptionBlockProps) => {
    return (
        <ExpandableTextBlock
            text={text}
            title="Exception"
            color="error"
            previewDirection="tail"
        />
    );
};
