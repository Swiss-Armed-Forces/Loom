import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";
import "@testing-library/jest-dom";

// runs a cleanup after each test case
afterEach(() => {
    cleanup();
});
