import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

BLUE, PURPLE = "#4285F4", "#5E35B1"

def render(series: dict, title: str, out_path: str) -> str:
    dates = series["dates"]; clicks = series["clicks"]; impressions = series["impressions"]
    t = series["totals"]
    fig = plt.figure(figsize=(12, 5.2), dpi=110); fig.patch.set_facecolor("white")

    tiles = [("Total clicks", f"{t['clicks']:,}", BLUE, "white"),
             ("Total impressions", f"{t['impressions']:,}", PURPLE, "white"),
             ("Average CTR", t["ctr"], "#F1F3F4", "#3c4043"),
             ("Average position", t["position"], "#F1F3F4", "#3c4043")]
    tax = fig.add_axes([0.06, 0.80, 0.9, 0.16]); tax.axis("off")
    tax.set_xlim(0, 4); tax.set_ylim(0, 1)
    for i, (label, val, bg, fg) in enumerate(tiles):
        tax.add_patch(FancyBboxPatch((i + 0.03, 0.05), 0.94, 0.9,
            boxstyle="round,pad=0.0,rounding_size=0.04", linewidth=0,
            facecolor=bg, mutation_aspect=0.25))
        sub = "white" if fg == "white" else "#5f6368"
        tax.text(i + 0.12, 0.62, label, color=sub, fontsize=10)
        tax.text(i + 0.12, 0.22, val, color=fg, fontsize=21, fontweight="bold")

    ax = fig.add_axes([0.06, 0.10, 0.88, 0.62]); ax2 = ax.twinx()
    ax.plot(dates, clicks, color=BLUE, linewidth=2.5, solid_capstyle="round")
    ax2.plot(dates, impressions, color=PURPLE, linewidth=2.5, solid_capstyle="round")
    cmax = max(clicks + [1]); imax = max(impressions + [1])
    ax.set_ylim(0, cmax * 1.15); ax2.set_ylim(0, imax * 1.15)
    ax.set_title("Clicks", loc="left", fontsize=10, color="#5f6368", pad=8)
    ax2.set_title("Impressions", loc="right", fontsize=10, color="#5f6368", pad=8)
    for a in (ax, ax2):
        a.tick_params(colors="#5f6368", labelsize=9, length=0)
        for s in a.spines.values(): s.set_visible(False)
    ax.spines["bottom"].set_visible(True); ax.spines["bottom"].set_color("#dadce0")
    ax.grid(axis="y", color="#e8eaed", linewidth=1); ax.set_axisbelow(True)
    fig.suptitle(title, x=0.06, y=0.99, ha="left", fontsize=15, color="#202124")

    fig.savefig(out_path, facecolor="white", bbox_inches="tight")
    plt.close(fig)
    return out_path
