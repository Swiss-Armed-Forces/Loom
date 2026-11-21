import i18n from "i18next";
import HttpBackend from "i18next-http-backend";
import { initReactI18next } from "react-i18next";

const basePath = import.meta.env.BASE_URL;

i18n.use(initReactI18next)
    .use(HttpBackend)
    .init({
        lng: "en",
        fallbackLng: "en",
        debug: true,
        backend: {
            loadPath: `${basePath}locales/{{lng}}/{{ns}}.json`,
        },
        // React escapes everything it renders, so i18next escaping on top of it
        // turns the quotes of an interpolated Lucene query into entities on screen.
        interpolation: { escapeValue: false },
    });
