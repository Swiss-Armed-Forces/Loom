import { Outlet } from "react-router-dom";
import LinearProgress from "@mui/material/LinearProgress";
import "./App.css";
import "react-toastify/dist/ReactToastify.css";
import { useAppSelector } from "./app/hooks";
import { selectIsLoading } from "./features/common/commonSlice";
import { ToastContainer } from "react-toastify";
import "./features/common/i18n";
import { Header } from "./features/common/header";

function App() {
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

            <Header />

            <Outlet />
        </div>
    );
}

export default App;
