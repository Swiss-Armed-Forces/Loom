import styles from "./ActivityBarLayout.module.css";

interface Props {
    top: React.ReactNode;
    bottom?: React.ReactNode;
    dataTour?: string;
    dataTourTop?: string;
    dataTourBottom?: string;
}

export const ActivityBarLayout = ({
    top,
    bottom,
    dataTour,
    dataTourTop,
    dataTourBottom,
}: Props) => (
    <div
        className={styles.activityBar}
        {...(dataTour !== undefined ? { "data-tour": dataTour } : {})}
    >
        <div
            className={styles.topSection}
            {...(dataTourTop !== undefined ? { "data-tour": dataTourTop } : {})}
        >
            {top}
        </div>
        {bottom !== undefined && (
            <div
                className={styles.bottomSection}
                {...(dataTourBottom !== undefined
                    ? { "data-tour": dataTourBottom }
                    : {})}
            >
                {bottom}
            </div>
        )}
    </div>
);
