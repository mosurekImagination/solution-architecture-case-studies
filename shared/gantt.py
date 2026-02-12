"""
Reusable Gantt chart generator for solution architecture case studies.
Uses matplotlib to produce PNG timeline visualizations.

Usage:
    from shared.gantt import create_gantt_chart

    tasks = [
        {"name": "Backend API", "stream": "Backend", "start": "2026-03-01", "end": "2026-05-15", "phase": "MVP"},
        {"name": "Mobile App",  "stream": "Frontend", "start": "2026-03-01", "end": "2026-06-01", "phase": "MVP"},
    ]
    milestones = [
        {"name": "POC Complete", "date": "2026-04-15"},
        {"name": "MVP Launch",   "date": "2026-06-30"},
    ]
    create_gantt_chart(tasks, milestones, title="Project Timeline", filename="01/diagrams/timeline-mvp")
"""

from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches


# Phase colors — consistent across all charts
PHASE_COLORS = {
    "POC":     "#4A90D9",   # Blue
    "MVP":     "#27AE60",   # Green
    "Full":    "#E67E22",   # Orange
    "Future":  "#95A5A6",   # Gray
}

# Stream alternating background colors for readability
STREAM_BG_COLORS = ["#F8F9FA", "#EBEDEF"]


def create_gantt_chart(
    tasks,
    milestones=None,
    title="Development Timeline",
    filename="gantt-chart",
    figsize=None,
    show_legend=True,
):
    """
    Create a Gantt chart PNG from task and milestone data.

    Args:
        tasks: List of dicts with keys:
            - name (str): Task name displayed on the bar
            - stream (str): Work stream grouping (e.g., "Backend", "Frontend")
            - start (str): Start date "YYYY-MM-DD"
            - end (str): End date "YYYY-MM-DD"
            - phase (str): One of "POC", "MVP", "Full", "Future"
            - team (str, optional): Team annotation (e.g., "2 devs")
        milestones: Optional list of dicts with keys:
            - name (str): Milestone name
            - date (str): Date "YYYY-MM-DD"
        title: Chart title
        filename: Output path without extension (e.g., "01/diagrams/timeline-mvp")
        figsize: Tuple (width, height) in inches. Auto-calculated if None.
        show_legend: Whether to show the phase legend
    """
    if not tasks:
        raise ValueError("At least one task is required")

    # Parse dates
    parsed_tasks = []
    for t in tasks:
        start = datetime.strptime(t["start"], "%Y-%m-%d")
        end = datetime.strptime(t["end"], "%Y-%m-%d")
        parsed_tasks.append({
            **t,
            "_start": start,
            "_end": end,
            "_duration": (end - start).days,
        })

    # Group tasks by stream (preserve order of first appearance)
    streams = []
    stream_tasks = {}
    for t in parsed_tasks:
        s = t["stream"]
        if s not in stream_tasks:
            streams.append(s)
            stream_tasks[s] = []
        stream_tasks[s].append(t)

    # Build flat list with y-positions (bottom to top for matplotlib)
    y_labels = []
    y_positions = []
    bar_data = []
    stream_boundaries = []  # (y_start, y_end, stream_name)

    y = 0
    for stream_idx, stream in enumerate(reversed(streams)):
        stream_start_y = y
        for task in reversed(stream_tasks[stream]):
            y_labels.append(task["name"])
            y_positions.append(y)
            bar_data.append(task)
            y += 1
        stream_boundaries.append((stream_start_y, y, stream))

    total_bars = len(y_labels)

    # Auto-calculate figure size
    if figsize is None:
        fig_height = max(4, 1.2 + total_bars * 0.5)
        fig_width = max(10, 14)
        figsize = (fig_width, fig_height)

    fig, ax = plt.subplots(figsize=figsize)

    # Draw stream background bands
    for i, (y_start, y_end, stream_name) in enumerate(stream_boundaries):
        bg_color = STREAM_BG_COLORS[i % len(STREAM_BG_COLORS)]
        ax.axhspan(y_start - 0.5, y_end - 0.5, facecolor=bg_color, alpha=0.5, zorder=0)
        # Stream label on the left (x=0.01 in axes fraction, y in data coords)
        mid_y = (y_start + y_end) / 2 - 0.5
        ax.text(
            0.01, mid_y, f"  {stream_name}",
            va="center", ha="left", fontsize=9, fontweight="bold",
            color="#555555", style="italic",
            transform=ax.get_yaxis_transform(),
            zorder=5,
        )

    # Draw task bars
    for i, (y_pos, task) in enumerate(zip(y_positions, bar_data)):
        color = PHASE_COLORS.get(task["phase"], "#BDC3C7")
        start_date = mdates.date2num(task["_start"])
        duration = task["_duration"]

        ax.barh(
            y_pos, duration, left=start_date,
            height=0.6, color=color, edgecolor="white",
            linewidth=0.8, zorder=3, alpha=0.9,
        )

        # Team annotation on the bar
        team_text = task.get("team", "")
        if team_text:
            bar_center_x = start_date + duration / 2
            ax.text(
                bar_center_x, y_pos, team_text,
                va="center", ha="center", fontsize=8,
                color="white", fontweight="bold", zorder=4,
            )

    # Draw milestones
    if milestones:
        for ms in milestones:
            ms_date = datetime.strptime(ms["date"], "%Y-%m-%d")
            ms_num = mdates.date2num(ms_date)
            ax.axvline(
                x=ms_num, color="#E74C3C", linewidth=1.5,
                linestyle="--", zorder=2, alpha=0.7,
            )
            ax.text(
                ms_num, total_bars - 0.3, f" {ms['name']}",
                va="bottom", ha="left", fontsize=8,
                color="#E74C3C", fontweight="bold",
                rotation=0, zorder=5,
            )

    # Formatting
    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels, fontsize=10)
    ax.set_ylim(-0.5, total_bars - 0.5)

    # X-axis: dates
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45, ha="right", fontsize=9)

    # Grid
    ax.grid(axis="x", alpha=0.3, linestyle="-", zorder=0)
    ax.set_axisbelow(True)

    # Title
    ax.set_title(title, fontsize=14, fontweight="bold", pad=15)

    # Legend
    if show_legend:
        legend_patches = [
            mpatches.Patch(color=color, label=phase)
            for phase, color in PHASE_COLORS.items()
        ]
        if milestones:
            legend_patches.append(
                plt.Line2D([0], [0], color="#E74C3C", linewidth=1.5,
                           linestyle="--", label="Milestone")
            )
        ax.legend(
            handles=legend_patches, loc="upper right",
            fontsize=9, framealpha=0.9, edgecolor="#CCCCCC",
        )

    # Remove top and right spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()

    # Save
    output_path = filename if filename.endswith(".png") else f"{filename}.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"✅ Gantt chart saved: {output_path}")
