import React from "react";
import { createRoot } from "react-dom/client";
import { Provider } from "react-redux";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { store } from "./app/store";
import App from "./App";
import "./main.css";
import { Search } from "./features/search/Search";
import { ThemeProvider } from "@mui/material";
import { globalTheme } from "./app/theme";
import { Home } from "./home";
import { Archives } from "./features/archives/Archives";

const container = document.getElementById("root")!;
const root = createRoot(container);

root.render(
    <React.StrictMode>
        <ThemeProvider theme={globalTheme}>
            <Provider store={store}>
                <BrowserRouter>
                    <Routes>
                        <Route path="/" element={<App />}>
                            <Route path="" element={<Home />} />
                            <Route path="search" element={<Search />} />
                            <Route path="archives" element={<Archives />} />
                        </Route>
                    </Routes>
                </BrowserRouter>
            </Provider>
        </ThemeProvider>
    </React.StrictMode>,
);
