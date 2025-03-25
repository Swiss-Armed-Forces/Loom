import styles from "./HighlightedSpan.module.css";

interface HighlightedSpanProps {
    children: React.ReactNode;
    isHighlighted: boolean;
    isClickable?: boolean;
}

export function HighlightedSpan({
    children,
    isHighlighted,
    isClickable,
}: HighlightedSpanProps) {
    const classNames = `${isHighlighted ? styles.highlighted : ""} ${
        isClickable ? styles.clickable : ""
    }`;
    return <span className={classNames}>{children}</span>;
}
