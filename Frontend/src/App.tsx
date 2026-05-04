import { LinearProgress } from "@mui/material";
import { Outlet } from "react-router-dom";
import "./App.css";
import "react-toastify/dist/ReactToastify.css";
import { ToastContainer } from "react-toastify";

import { useAppSelector } from "@app/hooks";
import { selectIsLoading } from "@app/slices/commonSlice";
import "@features/common/i18n";
import { DialogContainer, Header } from "@features/common/components";

const App = () => {
    const fetching = useAppSelector(selectIsLoading);

    return (
        <div className="app">
            {fetching && (
                <div className="loadingIndicator">
                    <LinearProgress color="primary" />
                </div>
            )}
            {!fetching && <div className="loadingIndicatorPlaceholder"></div>}

            <ToastContainer
                position="top-right"
                theme="colored"
                autoClose={5000}
                hideProgressBar={false}
                rtl={false}
                pauseOnFocusLoss
                draggable
                pauseOnHover
            />
            <DialogContainer />
            <Header />

            <Outlet />
        </div>
    );
};

export default App;
