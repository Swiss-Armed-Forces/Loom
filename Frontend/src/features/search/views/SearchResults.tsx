import { useTour } from "@app/tours/useTour";
import { EmptySearchResults } from "@features/search/components";

import { DetailedView } from "./Detailed/DetailedView";

export const SearchResults = () => {
    const { showQueryOverview } = useTour();

    if (showQueryOverview) return <EmptySearchResults forceQueryOverview />;
    return <DetailedView />;
};
