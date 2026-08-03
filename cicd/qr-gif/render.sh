#!/usr/bin/env nix-shell
#!nix-shell -i bash -p ffmpeg imagemagick gifsicle inkscape
# shellcheck shell=bash

# render.sh
# Generates optimized looping GIF animations transitioning between two SVG images.
# Usage: ./gif-transitions.sh before.svg after.svg

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
# Size variants — one GIF is produced per size per transition
SIZE_LABELS=(small  big)
SIZE_WIDTHS=( 400   800)

# Active canvas size — set per-iteration in main, used throughout
RENDER_WIDTH=800
RENDER_HEIGHT=800
PAD_COLOR=black            # letterbox/pillarbox fill color (any FFmpeg color name or hex)
TRANSITION_DURATION=1.0   # seconds
FPS=25

# Idle crackle animation (shown between transitions)
# Strategy: sparse bursts of crackle separated by long static frames, so
# total idle frames = CRACKLE_BURSTS*(CRACKLE_FRAMES_PER_BURST) + (CRACKLE_BURSTS+1)
# instead of IDLE_DURATION*IDLE_FPS — far smaller GIF for long idle periods.
IDLE_DURATION=30           # total seconds each still is shown per loop
CRACKLE_BURSTS=2           # number of crackle events during the idle period
CRACKLE_FRAMES_PER_BURST=5 # frames per crackle burst
CRACKLE_FPS=8              # frame rate within a crackle burst
MAX_GLITCH_LINES=4         # max glitch strips per crackle frame
MAX_GLITCH_SHIFT=12        # max horizontal pixel shift of a glitch strip
MAX_GLITCH_HEIGHT=6        # max height in pixels of a glitch strip
TMPDIR_PREFIX="gif_transitions"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
die() { echo "ERROR: $*" >&2; exit 1; }

usage() {
    echo "Usage: $0 before.svg after.svg"
    echo "Generates one GIF per FFmpeg xfade transition into output/"
    exit 1
}

# Render an SVG to a PNG at RENDER_WIDTH, preserving natural aspect ratio.
# No padding here — normalize_canvases aligns both images after both are rendered.
render_svg() {
    local svg="$1" out="$2"
    inkscape \
        --export-type=png \
        --export-filename="${out}" \
        --export-width="${RENDER_WIDTH}" \
        "${svg}" 2>/dev/null
}

# Pad both PNGs to a common canvas size so every frame is identical in dimensions.
# Height = max of the two natural heights; width = RENDER_WIDTH.
# Also updates the global RENDER_HEIGHT so FFmpeg and ImageMagick use the right size.
normalize_canvases() {
    local png_a="$1" png_b="$2"
    local h_a h_b
    h_a=$(magick identify -format "%h" "${png_a}")
    h_b=$(magick identify -format "%h" "${png_b}")
    RENDER_HEIGHT=$(( h_a > h_b ? h_a : h_b ))

    for png in "${png_a}" "${png_b}"; do
        local tmp="${png%.png}_norm.png"
        magick "${png}" \
            -background "${PAD_COLOR}" \
            -gravity center \
            -extent "${RENDER_WIDTH}x${RENDER_HEIGHT}" \
            "${tmp}"
        mv "${tmp}" "${png}"
    done
}

# Generate N crackle frames from a base PNG.
# Each frame = base image + 1..MAX_GLITCH_LINES randomly chosen glitch effects.
# Gaussian noise is intentionally omitted: it destroys LZW compression.
# Available effects (chosen randomly per glitch event):
#   0  horizontal strip shift  — slide a row band left or right
#   1  strip inversion         — B&W-negate a row band (very visible on QR codes)
#   2  vertical strip shift    — slide a column band up or down
#   3  ghost strip             — copy a row band and overdraw it elsewhere
generate_crackle_frames() {
    local base_png="$1" outdir="$2" n_frames="$3"
    local w=${RENDER_WIDTH} h=${RENDER_HEIGHT}

    local i
    for i in $(seq 1 "${n_frames}"); do
        local outfile
        outfile=$(printf "%s/crackle_%04d.png" "${outdir}" "${i}")
        local work="${outdir}/work_${i}"
        mkdir -p "${work}"

        local num_glitches=$(( RANDOM % MAX_GLITCH_LINES + 1 ))
        local current="${base_png}"

        local g
        for g in $(seq 1 "${num_glitches}"); do
            local next="${work}/glitch_${g}.png"
            local effect_type=$(( RANDOM % 4 ))
            local strip_h strip_w x y shift roll_arg src_y dst_y
            local ok=0

            case "${effect_type}" in
                0) # Horizontal strip shift: slide a row band left or right
                    strip_h=$(( RANDOM % MAX_GLITCH_HEIGHT + 1 ))
                    y=$(( RANDOM % (h - strip_h) ))
                    shift=$(( (RANDOM % (MAX_GLITCH_SHIFT * 2 + 1)) - MAX_GLITCH_SHIFT ))
                    [[ "${shift}" -eq 0 ]] && shift=1
                    roll_arg=$(printf "%+d+0" "${shift}")
                    magick "${current}" \
                        \( +clone -crop "${w}x${strip_h}+0+${y}" +repage \
                            -roll "${roll_arg}" \) \
                        -geometry "+0+${y}" -composite \
                        "${next}" 2>/dev/null && ok=1
                    ;;
                1) # Strip inversion: negate a row band (black/white swap)
                    strip_h=$(( RANDOM % MAX_GLITCH_HEIGHT + 1 ))
                    y=$(( RANDOM % (h - strip_h) ))
                    magick "${current}" \
                        \( +clone -crop "${w}x${strip_h}+0+${y}" +repage \
                            -negate \) \
                        -geometry "+0+${y}" -composite \
                        "${next}" 2>/dev/null && ok=1
                    ;;
                2) # Vertical strip shift: slide a column band up or down
                    strip_w=$(( RANDOM % (MAX_GLITCH_HEIGHT * 2) + 2 ))
                    x=$(( RANDOM % (w - strip_w) ))
                    shift=$(( (RANDOM % (MAX_GLITCH_SHIFT * 2 + 1)) - MAX_GLITCH_SHIFT ))
                    [[ "${shift}" -eq 0 ]] && shift=1
                    roll_arg=$(printf "+0%+d" "${shift}")
                    magick "${current}" \
                        \( +clone -crop "${strip_w}x${h}+${x}+0" +repage \
                            -roll "${roll_arg}" \) \
                        -geometry "+${x}+0" -composite \
                        "${next}" 2>/dev/null && ok=1
                    ;;
                3) # Ghost strip: copy a row band and paste it at a random y position
                    strip_h=$(( RANDOM % (MAX_GLITCH_HEIGHT * 3) + 4 ))
                    src_y=$(( RANDOM % (h - strip_h) ))
                    dst_y=$(( RANDOM % (h - strip_h) ))
                    magick "${current}" \
                        \( +clone -crop "${w}x${strip_h}+0+${src_y}" +repage \) \
                        -geometry "+0+${dst_y}" -composite \
                        "${next}" 2>/dev/null && ok=1
                    ;;
                *) ;;
            esac

            # On success advance; on failure keep current frame (graceful degradation)
            [[ "${ok}" -eq 1 ]] && current="${next}"
        done

        cp "${current}" "${outfile}"
        rm -rf "${work}"
    done
}

# Use FFmpeg xfade to render only the transition frames (no still frames)
# Writes individual PNGs: frame_0000.png, frame_0001.png, ...
render_transition_frames() {
    local img_a="$1" img_b="$2" effect="$3" outdir="$4"

    # Total frames for the transition
    local n_frames
    n_frames=$(echo "${TRANSITION_DURATION} * ${FPS}" | bc | cut -d. -f1)
    [[ "${n_frames}" -lt 1 ]] && n_frames=1

    # Inputs are already RENDER_WIDTH x RENDER_HEIGHT (normalized in render_svg).
    # xfade offset=0: transition starts immediately (we only want the transition, not stills)
    ffmpeg -y \
        -loop 1 -t "${TRANSITION_DURATION}" -i "${img_a}" \
        -loop 1 -t "${TRANSITION_DURATION}" -i "${img_b}" \
        -filter_complex \
            "[0:v]scale=${RENDER_WIDTH}:${RENDER_HEIGHT}:flags=lanczos,format=rgba[v0]; \
            [1:v]scale=${RENDER_WIDTH}:${RENDER_HEIGHT}:flags=lanczos,format=rgba[v1]; \
            [v0][v1]xfade=transition=${effect}:duration=${TRANSITION_DURATION}:offset=0,format=rgba[out]" \
        -map "[out]" \
        -vframes "${n_frames}" \
        -vsync vfr \
        "${outdir}/frame_%04d.png" \
        2>/dev/null
}

# Check whether an xfade transition name is supported by the installed ffmpeg
is_transition_supported() {
    local effect="$1"
    # Attempt a 1-frame probe; suppress all output
    ffmpeg -y \
        -f lavfi -i "color=black:size=${RENDER_WIDTH}x${RENDER_HEIGHT}:duration=0.04:rate=${FPS}" \
        -f lavfi -i "color=white:size=${RENDER_WIDTH}x${RENDER_HEIGHT}:duration=0.04:rate=${FPS}" \
        -filter_complex \
            "[0:v][1:v]xfade=transition=${effect}:duration=0.04:offset=0[out]" \
        -map "[out]" \
        -vframes 1 \
        -f null - \
        2>/dev/null
}

# Build a single optimized GIF for one transition effect.
# Frame 0 is a clean still of image A, so image viewers show a readable QR code.
# The loop is naturally seamless: B->A ends on image A, idle-A starts on image A.
# Sequence: idle-A -> [A->B] -> idle-B -> [B->A] -> loop
build_gif() {
    local img_a="$1" img_b="$2" effect="$3" outfile="$4" workdir="$5"

    local frames_ab="${workdir}/ab"
    local frames_ba="${workdir}/ba"
    local crackle_a="${workdir}/crackle_a"
    local crackle_b="${workdir}/crackle_b"
    mkdir -p "${frames_ab}" "${frames_ba}" "${crackle_a}" "${crackle_b}"

    # Render transition frames
    render_transition_frames "${img_a}" "${img_b}" "${effect}" "${frames_ab}"
    local rc_ab=$?; [[ ${rc_ab} -eq 0 ]] || return 1
    render_transition_frames "${img_b}" "${img_a}" "${effect}" "${frames_ba}"
    local rc_ba=$?; [[ ${rc_ba} -eq 0 ]] || return 1

    local n_ab n_ba
    n_ab=$(find "${frames_ab}" -name 'frame_*.png' 2>/dev/null | wc -l)
    n_ba=$(find "${frames_ba}" -name 'frame_*.png' 2>/dev/null | wc -l)
    [[ "${n_ab}" -lt 1 || "${n_ba}" -lt 1 ]] && return 1

    # Generate sparse crackle frames: CRACKLE_BURSTS * CRACKLE_FRAMES_PER_BURST total
    local n_crackle=$(( CRACKLE_BURSTS * CRACKLE_FRAMES_PER_BURST ))
    [[ "${n_crackle}" -lt 1 ]] && n_crackle=1
    generate_crackle_frames "${img_a}" "${crackle_a}" "${n_crackle}"
    generate_crackle_frames "${img_b}" "${crackle_b}" "${n_crackle}"

    # Frame delays in centiseconds
    local crackle_cs trans_cs static_cs total_crackle_cs
    crackle_cs=$(( 100 / CRACKLE_FPS ))
    [[ "${crackle_cs}" -lt 1 ]] && crackle_cs=1
    trans_cs=$(echo "scale=0; 100 / ${FPS}" | bc)
    [[ "${trans_cs}" -lt 1 ]] && trans_cs=1
    # Remaining idle time divided evenly across (CRACKLE_BURSTS+1) static gaps
    total_crackle_cs=$(( CRACKLE_BURSTS * CRACKLE_FRAMES_PER_BURST * crackle_cs ))
    static_cs=$(( (IDLE_DURATION * 100 - total_crackle_cs) / (CRACKLE_BURSTS + 1) ))
    [[ "${static_cs}" -lt 1 ]] && static_cs=1

    # Assemble: idle-A | [A->B] | idle-B | [B->A] -> loop back to idle-A (seamless)
    # Idle pattern: [static] [crackle burst] [static] [crackle burst] ... [static]
    local convert_args=()
    local burst _i frame_idx

    # --- Idle A (frame 0 = clean image A — readable QR code) ---
    frame_idx=1
    for burst in $(seq 0 "${CRACKLE_BURSTS}"); do
        convert_args+=(-delay "${static_cs}" "${img_a}")
        if [[ "${burst}" -lt "${CRACKLE_BURSTS}" ]]; then
            convert_args+=(-delay "${crackle_cs}")
            for _i in $(seq 1 "${CRACKLE_FRAMES_PER_BURST}"); do
                convert_args+=("$(printf "%s/crackle_%04d.png" "${crackle_a}" "${frame_idx}")")
                (( frame_idx++ )) || true
            done
        fi
    done

    # --- Transition A->B ---
    convert_args+=(-delay "${trans_cs}")
    while IFS= read -r f; do convert_args+=("${f}"); done \
        < <(find "${frames_ab}" -name 'frame_*.png' || true | sort || true)

    # --- Idle B ---
    frame_idx=1
    for burst in $(seq 0 "${CRACKLE_BURSTS}"); do
        convert_args+=(-delay "${static_cs}" "${img_b}")
        if [[ "${burst}" -lt "${CRACKLE_BURSTS}" ]]; then
            convert_args+=(-delay "${crackle_cs}")
            for _i in $(seq 1 "${CRACKLE_FRAMES_PER_BURST}"); do
                convert_args+=("$(printf "%s/crackle_%04d.png" "${crackle_b}" "${frame_idx}")")
                (( frame_idx++ )) || true
            done
        fi
    done

    # --- Transition B->A (ends on clean image A — seamless loop back to idle-A) ---
    convert_args+=(-delay "${trans_cs}")
    while IFS= read -r f; do convert_args+=("${f}"); done \
        < <(find "${frames_ba}" -name 'frame_*.png' || true | sort || true)

    local raw_gif="${workdir}/raw.gif"

    magick \
        -size "${RENDER_WIDTH}x${RENDER_HEIGHT}" \
        "${convert_args[@]}" \
        -coalesce \
        -layers optimize \
        -loop 0 \
        "${raw_gif}" 2>/dev/null || return 1

    gifsicle \
        --optimize=3 \
        --colors 16 \
        --loopcount=forever \
        "${raw_gif}" \
        -o "${outfile}" 2>/dev/null || cp "${raw_gif}" "${outfile}"
}

# Generate the index.html gallery
generate_html() {
    local outdir="$1"
    shift
    local gifs=("$@")

    local html="${outdir}/index.html"

    cat > "${html}" <<'HTML_HEADER'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GIF Transitions Gallery</title>
<style>
  body { font-family: system-ui, sans-serif; background: #111; color: #eee; margin: 0; padding: 2rem; }
  h1 { text-align: center; margin-bottom: 2rem; font-size: 1.6rem; letter-spacing: 0.05em; }
  .gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1.5rem; }
  .card { background: #1e1e1e; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.5); }
  .card img { width: 100%; display: block; }
  .card-title { padding: 0.6rem 1rem; font-size: 0.85rem; text-align: center;
                letter-spacing: 0.04em; color: #aaa; background: #181818; }
  .card-size { font-size: 0.75rem; color: #666; }
</style>
</head>
<body>
<h1>GIF Transitions Gallery</h1>
<div class="gallery">
HTML_HEADER

    for gif in "${gifs[@]}"; do
        local name size_kb
        name=$(basename "${gif}" .gif)
        size_kb=$(du -k "${gif}" | cut -f1)
        cat >> "${html}" <<HTML_CARD
  <div class="card">
    <img src="$(basename "${gif}")" alt="${name}" loading="lazy">
    <div class="card-title">${name} <span class="card-size">(${size_kb} KB)</span></div>
  </div>
HTML_CARD
    done

    cat >> "${html}" <<'HTML_FOOTER'
</div>
</body>
</html>
HTML_FOOTER

    echo "Gallery: ${html}"
}

# ---------------------------------------------------------------------------
# All known xfade transitions (as of FFmpeg 6.x)
# ---------------------------------------------------------------------------
ALL_TRANSITIONS=(
    pixelize
)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    [[ $# -ne 2 ]] && usage
    local svg_a="$1" svg_b="$2"
    [[ -f "${svg_a}" ]] || die "File not found: ${svg_a}"
    [[ -f "${svg_b}" ]] || die "File not found: ${svg_b}"

    # Check dependencies
    for cmd in ffmpeg magick gifsicle inkscape bc; do
        command -v "${cmd}" &>/dev/null || die "Required command not found: ${cmd}"
    done

    local outdir="output"
    mkdir -p "${outdir}"

    # Create a temp workspace
    local tmpdir
    tmpdir=$(mktemp -d "/tmp/${TMPDIR_PREFIX}.XXXXXX")
    trap '[[ -n "${tmpdir:-}" ]] && rm -rf "${tmpdir}"' EXIT

    local generated_gifs=()
    local skipped=0 built=0

    local si
    for si in "${!SIZE_LABELS[@]}"; do
        local size_label="${SIZE_LABELS[${si}]}"
        RENDER_WIDTH="${SIZE_WIDTHS[${si}]}"

        echo ""
        echo "=== Size: ${size_label} (width ${RENDER_WIDTH}px) ==="

        # Render SVGs fresh at this width
        local png_a="${tmpdir}/a_${size_label}.png"
        local png_b="${tmpdir}/b_${size_label}.png"
        echo "Rendering SVGs..."
        render_svg "${svg_a}" "${png_a}"
        render_svg "${svg_b}" "${png_b}"
        normalize_canvases "${png_a}" "${png_b}"
        echo "  canvas: ${RENDER_WIDTH}x${RENDER_HEIGHT}"

        echo "Generating transitions..."
        for effect in "${ALL_TRANSITIONS[@]}"; do
            printf "  %-20s " "${effect}"

            is_transition_supported "${effect}"
            local ts_rc=$?
            if [[ ${ts_rc} -ne 0 ]]; then
                echo "[skipped - not supported]"
                (( skipped++ )) || true
                continue
            fi

            local work="${tmpdir}/${size_label}_${effect}"
            mkdir -p "${work}"
            local outgif="${outdir}/${effect}_${size_label}.gif"

            build_gif "${png_a}" "${png_b}" "${effect}" "${outgif}" "${work}"
            local bg_rc=$?
            if [[ ${bg_rc} -eq 0 ]]; then
                local size_kb
                size_kb=$(du -k "${outgif}" | cut -f1)
                echo "[ok] ${size_kb} KB -> ${outgif}"
                generated_gifs+=("${outgif}")
                (( built++ )) || true
            else
                echo "[failed]"
                (( skipped++ )) || true
            fi
        done
    done

    echo ""
    echo "Results: ${built} GIFs generated, ${skipped} skipped/failed."

    if [[ ${#generated_gifs[@]} -gt 0 ]]; then
        generate_html "${outdir}" "${generated_gifs[@]}"
    else
        echo "No GIFs were generated."
        exit 1
    fi
}

main "$@"
