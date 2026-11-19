import { GetFilePreviewResponse } from "@app/api";

/** The two per-file attributes a card writes into its own text. */
export type FileStateInput = Pick<GetFilePreviewResponse, "flagged" | "seen">;

export interface FileStateStyle {
    color: string | undefined;
    fontWeight: "bold" | undefined;
}

/**
 * How a card draws text that stands for the file's own state.
 *
 * Two independent channels, the same rule `resultCardSurfaceStyle` paints the
 * surface by: weight carries read state and colour carries the flag, so a
 * flagged unseen file is bold and red rather than one or the other. Weight is
 * the non-colour half, which is what keeps the distinction readable in
 * greyscale.
 *
 * Shared by the header path and by the card fields the reader marks, so the
 * two cannot drift into meaning different things on the same card.
 */
export const fileStateStyle = ({
    flagged,
    seen,
}: FileStateInput): FileStateStyle => ({
    color: flagged ? "red" : undefined,
    fontWeight: seen ? undefined : "bold",
});
