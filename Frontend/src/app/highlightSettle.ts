/**
 * How long the highlight has to sit still before anything acts on it.
 *
 * Holding a move key walks the highlight over every card in between, and two
 * things would otherwise react to each one: the auto-actions middleware, which
 * `PUT`s per enabled action, and the File Detail sidebar's following tab, which
 * fetches a preview and a whole document. Neither is what the reader asked for
 * on the way past, so both wait for the highlight to come to rest.
 *
 * One constant because the two have to agree: a sidebar that loaded a file the
 * middleware had not yet marked seen would show it unseen and then correct
 * itself.
 */
export const HIGHLIGHT_SETTLE_MS = 300;
