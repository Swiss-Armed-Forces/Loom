import { Container, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { toast } from "react-toastify";
import { useAppDispatch } from "../../app/hooks";
import { getAll } from "../../app/api";

import { fillArchives } from "./archiveSlice";
import { TableView } from "./container/TableView";

export function Archives() {
    const { t } = useTranslation();
    const dispatch = useAppDispatch();

    getAll()
        .then((result) => {
            dispatch(fillArchives(result));
        })
        .catch((err) => {
            toast.error("Error while loading archives: " + err);
        });

    return (
        <Container>
            <Typography variant="h2">{t("archives.title")}</Typography>
            <TableView></TableView>
        </Container>
    );
}
