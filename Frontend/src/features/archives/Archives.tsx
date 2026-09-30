import { Container, useMediaQuery } from "@mui/material";
import { toast } from "react-toastify";

import { getAll } from "@app/api";
import { useAppDispatch } from "@app/hooks";
import { fillArchives } from "@app/slices/archiveSlice";

import styles from "./Archives.module.css";
import { ArchivesActivityBar } from "./components/ArchivesActivityBar/ArchivesActivityBar";
import { TableView } from "./views/TableView";

export const Archives = () => {
    const dispatch = useAppDispatch();
    const matchMedia = useMediaQuery("(max-width: 2200px)");
    const isMobile = useMediaQuery("(max-width: 600px)");

    getAll()
        .then((result) => {
            dispatch(fillArchives(result));
        })
        .catch((err) => {
            toast.error("Error while loading archives: " + err);
        });

    return (
        <div className={styles.archivesWrapper}>
            {!isMobile && <ArchivesActivityBar position="top" />}
            <Container className={styles.archivesContainer} maxWidth={false}>
                <div
                    className={styles.archivesContent}
                    style={{
                        width: isMobile ? "100%" : matchMedia ? "95%" : "80%",
                    }}
                >
                    <TableView />
                </div>
            </Container>
            {isMobile && <ArchivesActivityBar position="bottom" />}
        </div>
    );
};
