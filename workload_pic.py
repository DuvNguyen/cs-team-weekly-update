# workload_pic.py — one person's workload row as a PNG, in the look of SD Friday's workload grid
# (dark row, name + "Nh/day expected" on the left, a bubble per weekday, two grey weekend dots).
import datetime as dt
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

from workload import bubble_status

WIDTH, HEIGHT, DPI = 900, 76, 100
CENTRE_Y = 34                                   # pixel row of the bubbles (labels sit above, in the top strip)
MIN_D, MAX_D = 22, 60                          # bubble diameter in px, like getBubbleSize in SD Friday's chart
BG, TEXT, MUTED = "#131d2e", "#ffffff", "#9aa7bb"
COLORS = {"under": "#60a5fa", "optimal": "#22c55e", "over": "#ef4444", "none": "#3a465a"}
_FIRST_X, _STEP, _GROUP = 330, 60, 300          # centre of the first bubble, gap between bubbles, gap between week groups


def slot_x(group: int, i: int) -> float:
    return _FIRST_X + group * _GROUP + i * _STEP


def diameter(hours: float, expected: float | None) -> float:
    if not hours:
        return 0
    return min(MIN_D + hours / max(expected or 7, 7) * 30, MAX_D)


def _plain(text: str, limit: int = 34) -> str:
    text = text.replace("$", r"\$")              # matplotlib would read $...$ as maths
    return text if len(text) <= limit else text[: limit - 1] + "…"


def render_row(name: str, expected: float | None, weeks: dict[str, dict[dt.date, float]], out_path: str) -> str:
    """One person, one picture: a group of Mon-Fri bubbles per labelled week (e.g. "This week", "Next week")."""
    fig = plt.figure(figsize=(WIDTH / DPI, HEIGHT / DPI), dpi=DPI, facecolor=BG)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, WIDTH)
    ax.set_ylim(0, HEIGHT)
    ax.invert_yaxis()                              # pixel rows count from the top, like CENTRE_Y
    ax.axis("off")
    ax.text(22, CENTRE_Y - 8, _plain(name), color=TEXT, fontsize=11, fontweight="bold", va="center", ha="left")
    ax.text(22, CENTRE_Y + 10, f"{expected or 7:g}h/day expected", color=MUTED, fontsize=8.5, va="center", ha="left")
    for g, (label, week) in enumerate(weeks.items()):
        ax.text((slot_x(g, 0) + slot_x(g, 4)) / 2, HEIGHT - 8, _plain(label, 24), color=MUTED, fontsize=8, va="center", ha="center")
        for i, hours in enumerate(h for _, h in sorted(week.items())):
            status = bubble_status(hours, expected)
            if status == "none":
                ax.add_patch(Circle((slot_x(g, i), CENTRE_Y), 7, color=COLORS["none"], lw=0))
                continue
            d = diameter(hours, expected)
            ax.add_patch(Circle((slot_x(g, i), CENTRE_Y), d / 2, color=COLORS[status], lw=0))
            ax.text(slot_x(g, i), CENTRE_Y, f"{round(hours, 2):g}h", color=TEXT, fontsize=8.5 if d > 30 else 7,
                    fontweight="bold", va="center", ha="center")
    fig.savefig(out_path, facecolor=BG, dpi=DPI)
    plt.close(fig)
    return out_path
