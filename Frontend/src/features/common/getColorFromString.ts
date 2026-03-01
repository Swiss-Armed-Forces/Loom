const FALLBACK_COLOR = "#FFD600";
const COLOR_PALETTE = [
    // Spectrum colors
    "#D32F2F",
    "#E53935",
    "#FF5722",
    "#FF6D00", // Red-Orange
    "#F57C00",
    "#FF9800",
    "#FFC107",
    "#FFD600", // Orange-Yellow
    "#FFEB3B",
    "#C6FF00",
    "#64DD17",
    "#00C853", // Yellow-Green
    "#43A047",
    "#00BFA5",
    "#1DE9B6",
    "#00BCD4", // Green-Cyan
    "#00B0FF",
    "#0091EA",
    "#2196F3",
    "#2979FF", // Cyan-Blue
    "#3D5AFE",
    "#5C6BC0",
    "#6200EA",
    "#7E57C2", // Blue-Violet
    "#9C27B0",
    "#AB47BC",
    "#E040FB",
    "#F50057", // Violet-Magenta
    "#FF4081",
    "#EC407A", // Magenta-Pink

    // Browns
    "#3E2723",
    "#5D4037",
    "#795548",
    "#A1887F",

    // Grays & Black
    "#000000",
    "#263238",
    "#546E7A",
    "#90A4AE",
    "#CFD8DC",
];

const getHashCode = (str: string): number => {
    let hash = 5381;

    for (let i = 0; i < str.length; i++) {
        hash = (hash << 5) + hash + str.charCodeAt(i); // hash * 33 + char
    }

    return Math.abs(hash);
};

export const getColorFromString = (str: string): string => {
    const color = COLOR_PALETTE[getHashCode(str) % COLOR_PALETTE.length];
    return color ?? FALLBACK_COLOR;
};

export const calculateLuminance = (color: string): number => {
    const hex = color.substring(1);
    const r = parseInt(hex.substring(0, 2), 16) / 255;
    const g = parseInt(hex.substring(2, 4), 16) / 255;
    const b = parseInt(hex.substring(4, 6), 16) / 255;
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};

export const getFontColorFromBackGroundColor = (
    backgroundColor: string,
): string => {
    return calculateLuminance(backgroundColor) > 0.5 ? "#000000" : "#ffffff";
};
