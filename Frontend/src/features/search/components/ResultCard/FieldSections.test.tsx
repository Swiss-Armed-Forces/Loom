import { render } from "@testing-library/react";
import { Provider } from "react-redux";
import { afterEach, describe, expect, it, vi } from "vitest";

import { GetFilePreviewResponse } from "@app/api";
import {
    setFieldLayout,
    setPreviewFields,
    setShowFieldNames,
} from "@app/slices/searchSlice";
import { store } from "@app/store";

import { FieldSections } from "./FieldSections";

vi.mock("react-i18next", () => ({
    useTranslation: () => ({ t: (key: string) => key }),
}));

const FILE_PREVIEW: GetFilePreviewResponse = {
    fileId: "f1",
    flagged: false,
    hidden: false,
    seen: false,
    contentIsTruncated: true,
    name: "mail.eml",
    path: "/Mail/Inbox/mail.eml",
    fileExtension: "eml",
    state: "indexed",
    fields: {
        from: { value: "alice@example.org" },
        subject: { value: "Re: invoice" },
        content: { value: "Dear Bob, please find", isTruncated: true },
    },
};

const renderSections = () =>
    render(
        <Provider store={store}>
            <FieldSections filePreview={FILE_PREVIEW} />
        </Provider>,
    );

const accordions = (container: HTMLElement) =>
    container.querySelectorAll(".MuiAccordion-root");

describe("FieldSections", () => {
    afterEach(() => {
        store.dispatch(setFieldLayout("compact"));
        store.dispatch(setPreviewFields(["content"]));
        store.dispatch(setShowFieldNames(true));
    });

    it("keeps the accordion for a truncated value only", () => {
        store.dispatch(setFieldLayout("compact"));
        store.dispatch(setPreviewFields(["from", "subject", "content"]));

        const { container } = renderSections();

        // An expand control earns its place only where the backend cut the
        // value short; from and subject are plain lines.
        expect(accordions(container)).toHaveLength(1);
        expect(container.textContent).toContain("from:alice@example.org");
        expect(container.textContent).toContain("subject:Re: invoice");
    });

    it("drops the field names and keeps the values", () => {
        store.dispatch(setPreviewFields(["from", "subject"]));

        store.dispatch(setShowFieldNames(false));
        const { container } = renderSections();

        expect(container.textContent).not.toContain("from:");
        expect(container.textContent).toContain("alice@example.org");
        expect(container.textContent).toContain("Re: invoice");
    });
});
