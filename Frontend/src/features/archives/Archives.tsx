import { Container, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";
import { useAppDispatch, useMatchMedia } from "../../app/hooks";
import { getAll } from "../../app/api";
import styles from "./Archives.module.css";

import { fillArchives } from "./archiveSlice";
import { TableView } from "./container/TableView";

export function Archives() {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const matchMedia = useMatchMedia(2200);
    const smallMatchMedia = useMatchMedia(1100);

    getAll()
        .then((result) => {
            dispatch(fillArchives(result));
        })
        .catch((err) => {
            toast.error("Error while loading archives: " + err);
        });

    return (
        <Container className={styles.archivesContainer} maxWidth={false}>
            <div
                className={styles.archivesContent}
                style={{
                    width: smallMatchMedia
                        ? "100%"
                        : matchMedia
                          ? "75%"
                          : "50%",
                }}
            >
                <Typography variant="h2">{t("archives.title")}</Typography>
                <TableView />
            </div>
        </Container>
    );
}
