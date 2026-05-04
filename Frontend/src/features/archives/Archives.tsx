import { Container, Typography, useMediaQuery } from "@mui/material";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";

import { getAll } from "@app/api";
import { useAppDispatch } from "@app/hooks";
import { fillArchives } from "@app/slices/archiveSlice";

import styles from "./Archives.module.css";
import { TableView } from "./views/TableView";

export const Archives = () => {
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
};
