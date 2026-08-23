import type { InteractiveFrontendTool } from "./types";

export const createAskUserTool = (): InteractiveFrontendTool => ({
    interactive: true,
    definition: {
        name: "ask_user",
        description:
            "Ask the user a clarifying question with a set of answer options. " +
            "Use this when you need to know the user's preference before proceeding. " +
            "The user will see clickable answer chips; their selection is returned " +
            "as the tool result. An 'Other…' option is always shown — if the user " +
            "picks it, the result will be 'other' and the user will provide their " +
            "answer in the next message.",
        parameters: {
            type: "object",
            properties: {
                question: {
                    type: "string",
                    description: "The question to display to the user.",
                },
                options: {
                    type: "array",
                    items: { type: "string" },
                    description:
                        "The answer choices to present as clickable chips.",
                },
            },
            required: ["question", "options"],
        },
    },
});
