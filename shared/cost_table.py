"""
Reusable cost table renderer for solution architecture case studies.
Uses matplotlib to produce styled PNG tables for CAPEX and OPEX breakdowns.

Usage:
    from shared.cost_table import create_capex_table, create_opex_table

    capex_phases = [
        {"phase": "POC", "duration": "2 months", "team": "4 devs", "rate": "$600/day",
         "base_cost": "$96,000", "risk": "25%", "total": "$120,000"},
        {"phase": "MVP", "duration": "3 months", "team": "6 devs", "rate": "$600/day",
         "base_cost": "$216,000", "risk": "30%", "total": "$280,800"},
    ]
    create_capex_table(capex_phases, title="CAPEX Breakdown", filename="01/diagrams/capex-breakdown")

    opex_items = [
        {"service": "AWS ECS", "monthly_cost": "$200", "notes": "2 tasks, t3.medium"},
        {"service": "RDS PostgreSQL", "monthly_cost": "$150", "notes": "db.t4g.large"},
    ]
    create_opex_table(opex_items, title="OPEX Breakdown", filename="01/diagrams/opex-breakdown")
"""

import matplotlib.pyplot as plt
import matplotlib


# Phase row colors
PHASE_ROW_COLORS = {
    "POC":     "#D6EAF8",   # Light blue
    "MVP":     "#D5F5E3",   # Light green
    "Full":    "#FDEBD0",   # Light orange
    "Future":  "#E5E8E8",   # Light gray
}

HEADER_COLOR = "#2C3E50"
HEADER_TEXT_COLOR = "white"
TOTAL_ROW_COLOR = "#F0F3F4"
BORDER_COLOR = "#BDC3C7"


def create_capex_table(
    phases,
    title="CAPEX Breakdown — Development Costs",
    filename="capex-breakdown",
    figsize=None,
    total_label="Total CAPEX",
):
    """
    Create a styled CAPEX breakdown table as PNG.

    Args:
        phases: List of dicts with keys:
            - phase (str): Phase name ("POC", "MVP", "Full", "Future")
            - duration (str): e.g., "2 months"
            - team (str): e.g., "4 devs"
            - rate (str): e.g., "$600/day"
            - base_cost (str): e.g., "$96,000"
            - risk (str): e.g., "25%"
            - total (str): e.g., "$120,000"
        title: Table title
        filename: Output path without extension
        figsize: Tuple (width, height). Auto-calculated if None.
        total_label: Label for the totals row
    """
    if not phases:
        raise ValueError("At least one phase is required")

    columns = ["Phase", "Duration", "Team", "Rate", "Base Cost", "Risk", "Total"]
    col_keys = ["phase", "duration", "team", "rate", "base_cost", "risk", "total"]

    # Build cell data
    cell_data = []
    row_colors = []
    for p in phases:
        row = [p.get(k, "") for k in col_keys]
        cell_data.append(row)
        row_colors.append(PHASE_ROW_COLORS.get(p.get("phase", ""), "#FFFFFF"))

    # Auto-calculate figure size
    n_rows = len(cell_data)
    if figsize is None:
        fig_width = max(10, len(columns) * 1.6)
        fig_height = max(2, 0.8 + (n_rows + 1) * 0.5)
        figsize = (fig_width, fig_height)

    fig, ax = plt.subplots(figsize=figsize)
    ax.axis("off")

    table = ax.table(
        cellText=cell_data,
        colLabels=columns,
        cellLoc="center",
        loc="center",
    )

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.6)

    # Style header row
    for j in range(len(columns)):
        cell = table[0, j]
        cell.set_facecolor(HEADER_COLOR)
        cell.set_text_props(color=HEADER_TEXT_COLOR, fontweight="bold")
        cell.set_edgecolor(BORDER_COLOR)

    # Style data rows
    for i in range(len(cell_data)):
        for j in range(len(columns)):
            cell = table[i + 1, j]
            cell.set_facecolor(row_colors[i])
            cell.set_edgecolor(BORDER_COLOR)
            # Bold the total column
            if j == len(columns) - 1:
                cell.set_text_props(fontweight="bold")

    # Title
    ax.set_title(title, fontsize=14, fontweight="bold", pad=20, color="#2C3E50")

    plt.tight_layout()

    output_path = filename if filename.endswith(".png") else f"{filename}.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"✅ CAPEX table saved: {output_path}")


def create_opex_table(
    services,
    title="OPEX Breakdown — Monthly Recurring Costs",
    filename="opex-breakdown",
    figsize=None,
    show_total=True,
):
    """
    Create a styled OPEX breakdown table as PNG.

    Args:
        services: List of dicts with keys:
            - service (str): Service name
            - monthly_cost (str): e.g., "$200"
            - notes (str): Additional notes
            - category (str, optional): "Infrastructure", "3rd Party", "Licensing", "Support"
        title: Table title
        filename: Output path without extension
        figsize: Tuple (width, height). Auto-calculated if None.
        show_total: Whether to add a totals row (auto-sums numeric costs)
    """
    if not services:
        raise ValueError("At least one service is required")

    columns = ["Service", "Monthly Cost", "Notes"]
    col_keys = ["service", "monthly_cost", "notes"]

    cell_data = []
    total_cost = 0
    for s in services:
        row = [s.get(k, "") for k in col_keys]
        cell_data.append(row)
        # Try to parse cost for totals
        cost_str = s.get("monthly_cost", "$0").replace("$", "").replace(",", "").strip()
        try:
            total_cost += float(cost_str)
        except ValueError:
            pass

    # Add total row
    if show_total:
        total_formatted = f"${total_cost:,.0f}"
        cell_data.append(["Total OPEX", total_formatted, ""])

    n_rows = len(cell_data)
    if figsize is None:
        fig_width = max(8, 12)
        fig_height = max(2, 0.8 + n_rows * 0.45)
        figsize = (fig_width, fig_height)

    fig, ax = plt.subplots(figsize=figsize)
    ax.axis("off")

    table = ax.table(
        cellText=cell_data,
        colLabels=columns,
        cellLoc="center",
        loc="center",
        colWidths=[0.3, 0.2, 0.5],
    )

    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.6)

    # Style header
    for j in range(len(columns)):
        cell = table[0, j]
        cell.set_facecolor(HEADER_COLOR)
        cell.set_text_props(color=HEADER_TEXT_COLOR, fontweight="bold")
        cell.set_edgecolor(BORDER_COLOR)

    # Style data rows (alternating)
    for i in range(len(cell_data)):
        is_total = show_total and i == len(cell_data) - 1
        for j in range(len(columns)):
            cell = table[i + 1, j]
            cell.set_edgecolor(BORDER_COLOR)
            if is_total:
                cell.set_facecolor(TOTAL_ROW_COLOR)
                cell.set_text_props(fontweight="bold")
            else:
                bg = "#FFFFFF" if i % 2 == 0 else "#F8F9FA"
                cell.set_facecolor(bg)
                # Notes column left-aligned
                if j == 2:
                    cell.set_text_props(ha="left")

    ax.set_title(title, fontsize=14, fontweight="bold", pad=20, color="#2C3E50")

    plt.tight_layout()

    output_path = filename if filename.endswith(".png") else f"{filename}.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"✅ OPEX table saved: {output_path}")


def create_cost_summary(
    options,
    title="Architecture Options — Cost Comparison",
    filename="cost-comparison",
    figsize=None,
):
    """
    Create a comparison chart of multiple architecture options.

    Args:
        options: List of dicts with keys:
            - name (str): Option name (e.g., "Option 1: MVP")
            - capex (float): Total CAPEX in dollars
            - opex_monthly (float): Monthly OPEX in dollars
            - timeline (str): e.g., "4 months"
            - features (str): Brief feature summary
        title: Chart title
        filename: Output path without extension
        figsize: Tuple (width, height). Auto-calculated if None.
    """
    if not options:
        raise ValueError("At least one option is required")

    n = len(options)
    if figsize is None:
        figsize = (max(10, n * 3), 6)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    names = [o["name"] for o in options]
    capex_values = [o["capex"] for o in options]
    opex_values = [o["opex_monthly"] for o in options]

    colors = ["#4A90D9", "#27AE60", "#E67E22", "#9B59B6", "#E74C3C"][:n]

    # CAPEX bar chart
    bars1 = ax1.bar(names, capex_values, color=colors, edgecolor="white", linewidth=0.8)
    ax1.set_title("CAPEX (Development)", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Cost ($)")
    ax1.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
        lambda x, p: f"${x:,.0f}"
    ))
    for bar, val in zip(bars1, capex_values):
        ax1.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height(),
            f"${val:,.0f}", ha="center", va="bottom", fontsize=9, fontweight="bold",
        )

    # OPEX bar chart
    bars2 = ax2.bar(names, opex_values, color=colors, edgecolor="white", linewidth=0.8)
    ax2.set_title("OPEX (Monthly)", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Cost ($/month)")
    ax2.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
        lambda x, p: f"${x:,.0f}"
    ))
    for bar, val in zip(bars2, opex_values):
        ax2.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height(),
            f"${val:,.0f}/mo", ha="center", va="bottom", fontsize=9, fontweight="bold",
        )

    for ax in [ax1, ax2]:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.sca(ax)
        plt.xticks(rotation=20, ha="right", fontsize=9)

    fig.suptitle(title, fontsize=14, fontweight="bold", y=1.02, color="#2C3E50")
    plt.tight_layout()

    output_path = filename if filename.endswith(".png") else f"{filename}.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"✅ Cost comparison saved: {output_path}")
