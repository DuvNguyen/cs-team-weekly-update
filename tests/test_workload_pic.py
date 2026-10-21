import datetime as dt
from PIL import Image
import workload_pic as pic

MON = dt.date(2026, 10, 19)
DAYS = [MON + dt.timedelta(days=i) for i in range(5)]


def week(*hours):
    return dict(zip(DAYS, hours))


def near(px, hex_colour, tol=12):
    rgb = [int(hex_colour[i:i + 2], 16) for i in (1, 3, 5)]
    return all(abs(a - b) <= tol for a, b in zip(px[:3], rgb))


def test_writes_a_png(tmp_path):
    out = pic.render_row("Le Minh Tri", 4, week(6.8, 8.2, 5.35, 4.05, 5.2), str(tmp_path / "row.png"))
    assert open(out, "rb").read(8) == b"\x89PNG\r\n\x1a\n"
    assert Image.open(out).size == (pic.WIDTH, pic.HEIGHT)


def test_bubble_colours_follow_status(tmp_path):
    # expected 7h: 5h is under (blue), 7h optimal (green), 9h over (red), 0h grey
    out = pic.render_row("Anyone", 7, week(5, 7, 9, 0, 0), str(tmp_path / "row.png"))
    im = Image.open(out).convert("RGB")
    for i, (hours, colour) in enumerate([(5, pic.COLORS["under"]), (7, pic.COLORS["optimal"]), (9, pic.COLORS["over"])]):
        cx, r = pic.slot_x(i), pic.diameter(hours, 7) / 2
        assert near(im.getpixel((round(cx - 0.8 * r), pic.HEIGHT // 2)), colour), f"slot {i} ({hours}h)"
    assert near(im.getpixel((round(pic.slot_x(3)), pic.HEIGHT // 2)), pic.COLORS["none"])


def test_bigger_workload_means_bigger_bubble():
    assert pic.diameter(3, 7) < pic.diameter(7, 7) < pic.diameter(10, 7) <= pic.MAX_D
    assert pic.diameter(0, 7) == 0


def test_zero_or_missing_expected_hours_does_not_crash(tmp_path):
    pic.render_row("X", 0, week(2, 0, 0, 0, 0), str(tmp_path / "a.png"))
    pic.render_row("X", None, week(2, 0, 0, 0, 0), str(tmp_path / "b.png"))


def test_odd_names_do_not_crash(tmp_path):
    pic.render_row("Nguyễn Thị $x$ & <b> " + "n" * 80, 7, week(1, 1, 1, 1, 1), str(tmp_path / "c.png"))


def test_caption_is_accepted(tmp_path):
    pic.render_row("Le Minh Tri", 4, week(1, 2, 3, 4, 5), str(tmp_path / "c.png"), caption="next week")
