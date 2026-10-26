
import csv
import os
import matplotlib.pyplot as plt

# --------------------------------------------------
# Configuration
# --------------------------------------------------
CSV_FILE = "results/results.csv"
GRAPH_DIR = "results/graphs"

os.makedirs(GRAPH_DIR, exist_ok=True)

# Electric Orchid palette
PURPLE = "#845EC2"
PINK = "#FF6F91"
GOLD = "#FFC75F"
SLATE = "#625778"
GRID = "#E5DDF2"
BACKGROUND = "#FAF8FF"

COLORS = {
    "DV": PURPLE,
    "LS": PINK,
}

plt.rcParams.update({
    "figure.facecolor": BACKGROUND,
    "axes.facecolor": BACKGROUND,
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 16,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "text.color": SLATE,
    "axes.labelcolor": SLATE,
    "xtick.color": SLATE,
    "ytick.color": SLATE,
    "savefig.facecolor": BACKGROUND,
    "savefig.dpi": 300,
})

# --------------------------------------------------
# Read experiment results
# --------------------------------------------------
with open(CSV_FILE, "r", newline="", encoding="utf-8") as file:
    experiments = list(csv.DictReader(file))

scenarios = [
    "Baseline",
    "Fresh start after failure",
    "Recovery after failure",
]

algorithms = ["DV", "LS"]

message_data = {}
round_data = {}

for scenario in scenarios:
    for algorithm in algorithms:
        row = next(
            (
                item for item in experiments
                if item["experiment"] == scenario
                and item["algorithm"] == algorithm
            ),
            None,
        )

        if row is None:
            raise ValueError(
                f"Missing result: {scenario} - {algorithm}"
            )

        message_data[(scenario, algorithm)] = int(
            row["message_count"]
        )
        round_data[(scenario, algorithm)] = int(row["rounds"])

# --------------------------------------------------
# Create charts
# --------------------------------------------------
def create_comparison_chart(data, ylabel, title, filename):
    positions = list(range(len(scenarios)))
    width = 0.32

    fig, ax = plt.subplots(figsize=(10, 6.2))
    fig.patch.set_facecolor(BACKGROUND)
    ax.set_facecolor(BACKGROUND)

    for index, algorithm in enumerate(algorithms):
        values = [
            data[(scenario, algorithm)]
            for scenario in scenarios
        ]

        offsets = [
            position + (index - 0.5) * width
            for position in positions
        ]

        bars = ax.bar(
            offsets,
            values,
            width,
            label=algorithm,
            color=COLORS[algorithm],
            edgecolor=BACKGROUND,
            linewidth=1.2,
            zorder=3,
        )

        ax.bar_label(
            bars,
            labels=[str(value) for value in values],
            padding=5,
            fontsize=10,
            fontweight="bold",
            color=COLORS[algorithm],
        )

    # Title and axis labels
    ax.set_title(
        title,
        loc="left",
        pad=24,
        color=PURPLE,
    )
    ax.set_ylabel(ylabel, labelpad=10)
    ax.set_xlabel("Experiment scenario", labelpad=12)

    ax.set_xticks(positions)
    ax.set_xticklabels([
        "Baseline",
        "Fresh Start\nAfter Failure",
        "Recovery\nAfter Failure",
    ])

    ax.tick_params(axis="x", length=0, pad=10)
    ax.tick_params(axis="y", length=0, pad=8)

    # Soft gridlines
    ax.set_axisbelow(True)
    ax.grid(
        axis="y",
        color=GRID,
        linewidth=0.9,
        linestyle="-",
        zorder=0,
    )
    ax.grid(axis="x", visible=False)

    # Minimal borders
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)

    ax.spines["bottom"].set_color(GRID)

    # Keep zero as the baseline and allow room for value labels
    max_value = max(
        data[(scenario, algorithm)]
        for scenario in scenarios
        for algorithm in algorithms
    )
    ax.set_ylim(0, max_value * 1.22 if max_value > 0 else 1)

    # Clean legend
    legend = ax.legend(
        title="Routing Algorithm",
        loc="upper right",
        frameon=False,
        ncol=2,
    )
    legend.get_title().set_color(PURPLE)

    for item in legend.get_texts():
        item.set_color(SLATE)

    fig.tight_layout(pad=2)

    output_path = os.path.join(GRAPH_DIR, filename)
    fig.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
        facecolor=BACKGROUND,
    )
    plt.close(fig)

    print(f"Graph saved: {output_path}")


# --------------------------------------------------
# Generate both graphs
# --------------------------------------------------
create_comparison_chart(
    message_data,
    "Message transmission attempts (count)",
    "DV vs LS | Message Overhead",
    "message_overhead.png",
)

create_comparison_chart(
    round_data,
    "Convergence rounds (count)",
    "DV vs LS | Convergence Rounds",
    "convergence_rounds.png",
)

print("\nBoth graphs generated successfully!")
