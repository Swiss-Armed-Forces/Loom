import { Close, Search } from "@mui/icons-material";
import { IconButton, InputAdornment, InputBase } from "@mui/material";

import styles from "./FilterBar.module.css";

interface FilterBarProps {
    value: string;
    onChange: (value: string) => void;
    /** Says what this bar filters. Doubles as the input's accessible name. */
    placeholder: string;
    /** Tour anchor, for the one bar a tour step points at. */
    dataTour?: string;
}

/**
 * The filter box a panel puts above its own list.
 *
 * Presentational only: the panel below it owns the text and decides what
 * filtering means, which is why two of them narrow an array already in hand while
 * the folder panel's runs a paginated search. Sharing the look is the whole of what
 * is shared.
 *
 * It sits outside the list's scroll container, so a panel using it scrolls its own
 * body rather than letting the sidebar scroll the bar away with it.
 */
export const FilterBar = ({
    value,
    onChange,
    placeholder,
    dataTour,
}: FilterBarProps) => (
    <div className={styles.filterBar} data-tour={dataTour}>
        <InputBase
            className={styles.filterInput}
            value={value}
            onChange={(event) => onChange(event.target.value)}
            placeholder={placeholder}
            inputProps={{ "aria-label": placeholder }}
            startAdornment={
                <InputAdornment position="start">
                    <Search fontSize="small" className={styles.filterIcon} />
                </InputAdornment>
            }
            endAdornment={
                value ? (
                    <InputAdornment position="end">
                        <IconButton
                            size="small"
                            onClick={() => onChange("")}
                            edge="end"
                        >
                            <Close
                                fontSize="small"
                                className={styles.filterIcon}
                            />
                        </IconButton>
                    </InputAdornment>
                ) : null
            }
        />
    </div>
);
