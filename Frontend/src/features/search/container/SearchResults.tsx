import { useAppSelector } from "../../../app/hooks";
import { DetailedView } from "./DetailedView";
import { FolderView } from "./folderview/FolderView.tsx";
import { StatisticsView } from "./StatisticsView";
import { SearchView, selectActiveSearchView } from "../searchSlice.ts";

export function SearchResults() {
    const searchView = useAppSelector(selectActiveSearchView);

    switch (searchView) {
        case SearchView.FOLDER:
            return <FolderView />;
        case SearchView.DETAILED:
            return <DetailedView />;
        case SearchView.STATISTICS:
            return <StatisticsView />;
        default:
            return <DetailedView />;
    }
}
