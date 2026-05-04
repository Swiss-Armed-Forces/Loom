import { useAppSelector } from "@app/hooks";
import { SearchView, selectActiveSearchView } from "@app/slices/searchSlice";

import { DetailedView } from "./Detailed/DetailedView";
import { FolderView } from "./Folder/FolderView";
import { StatisticsView } from "./Statistics/StatisticsView";

export const SearchResults = () => {
    const searchView = useAppSelector(selectActiveSearchView);

    switch (searchView) {
        case SearchView.FOLDER:
            return <FolderView />;
        case SearchView.STATISTICS:
            return <StatisticsView />;
        case SearchView.DETAILED:
        default:
            return <DetailedView />;
    }
};
