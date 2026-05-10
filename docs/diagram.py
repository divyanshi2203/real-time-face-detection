"""Generate ``docs/architecture.png``.

Run from the repo root:

    pip install matplotlib
    python docs/diagram.py

The resulting PNG is committed alongside this script so reviewers can view
the diagram without running anything, but it is fully reproducible.
"""
import os

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = os.path.join(os.path.dirname(__file__), "architecture.png")


def box(ax, x, y, w, h, label, color):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.08",
        linewidth=1.4, edgecolor="#0f172a", facecolor=color,
    ))
    ax.text(x + w / 2, y + h / 2, label,
            ha="center", va="center",
            color="white", fontsize=11, weight="bold")


def arrow(ax, x1, y1, x2, y2, label="", lab_dx=0.0, lab_dy=0.0):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>", mutation_scale=14,
        color="#0f172a", linewidth=1.3,
    ))
    if label:
        ax.text((x1 + x2) / 2 + lab_dx, (y1 + y2) / 2 + lab_dy, label,
                ha="center", va="center",
                fontsize=9, color="#0f172a",
                bbox=dict(boxstyle="round,pad=0.25",
                          fc="white", ec="#cbd5e1"))


def main():
    fig, ax = plt.subplots(figsize=(13, 8))
    fig.patch.set_facecolor("white")
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 9)
    ax.axis("off")

    ax.text(6, 8.55, "Real-Time Face Detection — System Architecture",
            ha="center", fontsize=15, weight="bold")

    # Lane separators
    for y in (6.6, 4.6, 2.4):
        ax.plot([0.3, 11.5], [y, y],
                color="#e2e8f0", linewidth=0.8, linestyle="--")

    # Lane labels (right-aligned, sitting in the gutter)
    for y, label in [(7.6, "CLIENT"), (5.6, "API"),
                     (3.6, "PROCESSING"), (1.4, "STORAGE")]:
        ax.text(12.9, y, label, ha="right", va="center",
                fontsize=9, color="#64748b", weight="bold")

    # CLIENT lane
    box(ax, 1.0, 7.0, 4.0, 1.2,
        "Browser\n(loads React from Flask)", "#1e293b")
    box(ax, 7.0, 7.0, 4.0, 1.2,
        "React (Vite build)\nupload · playback · ROI table", "#0f766e")
    arrow(ax, 5.05, 7.6, 6.95, 7.6)

    # CLIENT -> API
    arrow(ax, 9.0, 7.0, 6.5, 6.2,
          "POST /api/videos\nGET  /api/videos/{id}\nGET  /api/videos/{id}/rois",
          lab_dx=2.4, lab_dy=0.4)

    # API lane
    box(ax, 4.0, 5.0, 4.0, 1.2,
        "Flask (gunicorn)\nrouting · validation · errors", "#1d4ed8")

    # API -> PROCESSING
    arrow(ax, 5.0, 5.0, 3.0, 4.2, "frames", lab_dx=-0.6, lab_dy=0.1)
    arrow(ax, 7.0, 5.0, 9.0, 4.2, "draw ROI", lab_dx=0.7, lab_dy=0.1)

    # PROCESSING lane
    box(ax, 1.0, 3.0, 4.0, 1.2,
        "Face Detection\nface_recognition (dlib)", "#7c3aed")
    box(ax, 7.0, 3.0, 4.0, 1.2,
        "Frame Renderer\nimageio + Pillow (no OpenCV)", "#9333ea")

    # PROCESSING -> STORAGE
    arrow(ax, 3.0, 3.0, 3.0, 2.0, "ROI rows", lab_dx=0.65)
    arrow(ax, 9.0, 3.0, 9.0, 2.0, "mp4", lab_dx=0.4)

    # STORAGE lane
    box(ax, 1.0, 0.8, 4.0, 1.2,
        "SQLite\nvideos · roi_frames", "#b45309")
    box(ax, 7.0, 0.8, 4.0, 1.2,
        "Filesystem\nuploaded · processed mp4", "#475569")

    plt.savefig(OUT, dpi=160, bbox_inches="tight", facecolor="white")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
