import { ThemeProvider } from "@mui/material";
import React from "react";
import { createRoot } from "react-dom/client";
import { Provider } from "react-redux";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import { store } from "@app/store";
import { globalTheme } from "@app/theme";
import { Archives } from "@features/archives/Archives";
import { Search } from "@features/search/Search";

import App from "./App";
import "./main.css";
import { Home } from "./home";

const container = document.getElementById("root")!;
const root = createRoot(container);

root.render(
    <React.StrictMode>
        <ThemeProvider theme={globalTheme}>
            <Provider store={store}>
                <BrowserRouter basename={import.meta.env.BASE_URL}>
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
