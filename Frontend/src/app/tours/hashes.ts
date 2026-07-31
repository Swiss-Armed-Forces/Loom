import { TourState, TourStep } from "./types";

export type TourStepHashes = Record<string, string>;

export interface TourCopyResolver {
    exists: (key: string) => boolean;
    translate: (key: string) => string;
}

const hashText = async (text: string): Promise<string> => {
    const digest = await crypto.subtle.digest(
        "SHA-256",
        new TextEncoder().encode(text),
    );
    return Array.from(new Uint8Array(digest), (byte) =>
        byte.toString(16).padStart(2, "0"),
    ).join("");
};

const getCanonicalStepCopy = (
    step: TourStep,
    translate: TourCopyResolver["translate"],
): readonly (string | null)[] => [
    translate(step.titleKey),
    translate(step.descriptionKey),
    step.doneButtonKey ? translate(step.doneButtonKey) : null,
    step.nextButtonKey ? translate(step.nextButtonKey) : null,
];

const getStepCopyKeys = (step: TourStep): readonly string[] => [
    step.titleKey,
    step.descriptionKey,
    ...(step.doneButtonKey ? [step.doneButtonKey] : []),
    ...(step.nextButtonKey ? [step.nextButtonKey] : []),
];

const validateTourSteps = (
    steps: readonly TourStep[],
    exists: TourCopyResolver["exists"],
): void => {
    const seenIds = new Set<string>();
    steps.forEach((step) => {
        if (seenIds.has(step.id)) {
            throw new Error(`Duplicate tour step ID: ${step.id}`);
        }
        seenIds.add(step.id);

        const missingKey = getStepCopyKeys(step).find((key) => !exists(key));
        if (missingKey) {
            throw new Error(
                `Missing English tour copy for step "${step.id}": ${missingKey}`,
            );
        }
    });
};

export const createTourStepHashes = async (
    steps: readonly TourStep[],
    resolver: TourCopyResolver,
): Promise<TourStepHashes> => {
    validateTourSteps(steps, resolver.exists);
    return Object.fromEntries(
        await Promise.all(
            steps.map(async (step) => [
                step.id,
                await hashText(
                    JSON.stringify(
                        getCanonicalStepCopy(step, resolver.translate),
                    ),
                ),
            ]),
        ),
    );
};

export const getUnacknowledgedTourSteps = (
    steps: readonly TourStep[],
    hashes: TourStepHashes,
    state: TourState,
): readonly TourStep[] =>
    steps.filter((step) => {
        const hash = hashes[step.id];
        return (
            hash !== undefined &&
            !state.acknowledgedStepHashes[step.id]?.includes(hash)
        );
    });

export const acknowledgeTourSteps = (
    state: TourState,
    steps: readonly TourStep[],
    hashes: TourStepHashes,
): TourState => {
    const acknowledgedStepHashes = { ...state.acknowledgedStepHashes };

    steps.forEach((step) => {
        const hash = hashes[step.id];
        if (!hash) return;
        const acknowledged = acknowledgedStepHashes[step.id] ?? [];
        if (!acknowledged.includes(hash)) {
            acknowledgedStepHashes[step.id] = [...acknowledged, hash];
        }
    });

    return { ...state, acknowledgedStepHashes };
};
