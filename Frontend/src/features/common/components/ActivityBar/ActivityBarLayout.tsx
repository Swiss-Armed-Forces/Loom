import styles from "./ActivityBarLayout.module.css";

interface Props {
    top: React.ReactNode;
    bottom?: React.ReactNode;
    dataTour?: string;
}

export const ActivityBarLayout = ({ top, bottom, dataTour }: Props) => (
    <div
        className={styles.activityBar}
        {...(dataTour !== undefined ? { "data-tour": dataTour } : {})}
    >
        <div className={styles.topSection}>{top}</div>
        {bottom !== undefined && (
            <div className={styles.bottomSection}>{bottom}</div>
        )}
    </div>
);
