import { Container, useMediaQuery } from "@mui/material";
import { toast } from "react-toastify";

import { getAll } from "@app/api";
import { useAppDispatch } from "@app/hooks";
import { fillArchives } from "@app/slices/archiveSlice";

import styles from "./Archives.module.css";
import { TableView } from "./views/TableView";

export const Archives = () => {
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
                          ? "95%"
                          : "80%",
                }}
            >
                <TableView />
            </div>
        </Container>
    );
};
