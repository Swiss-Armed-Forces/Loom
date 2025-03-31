import { Container, Typography, useMediaQuery } from "@mui/material";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";
import { useAppDispatch } from "../../app/hooks";
import { getAll } from "../../app/api";
import styles from "./Archives.module.css";

import { fillArchives } from "./archiveSlice";
import { TableView } from "./container/TableView";

export function Archives() {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();
    const matchMedia = useMediaQuery("(max-width: 2200px)");
    const smallMatchMedia = useMediaQuery("(max-width: 1100px)");

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
