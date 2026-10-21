import datetime as dt
from PIL import Image
import workload_pic as pic

MON = dt.date(2026, 10, 19)
DAYS = [MON + dt.timedelta(days=i) for i in range(5)]
NEXT = [d + dt.timedelta(days=7) for d in DAYS]


def week(*hours, days=DAYS):
    return dict(zip(days, hours))


def both(this, nxt):
    return {"This week": week(*this), "Next week": week(*nxt, days=NEXT)}


def near(px, hex_colour, tol=12):
    rgb = [int(hex_colour[i:i + 2], 16) for i in (1, 3, 5)]
    return all(abs(a - b) <= tol for a, b in zip(px[:3], rgb))


def centre_pixel(im, group, i, hours, expected, side=0.8):
    r = pic.diameter(hours, expected) / 2
    return im.getpixel((round(pic.slot_x(group, i) - side * r), pic.CENTRE_Y))


def test_writes_a_png_with_both_weeks_in_one_picture(tmp_path):
    out = pic.render_row("Le Minh Tri", 4, both([6.8, 8.2, 5.35, 4.05, 5.2], [1, 2, 3, 4, 5]), str(tmp_path / "row.png"))
    assert open(out, "rb").read(8) == b"\x89PNG\r\n\x1a\n"
    assert Image.open(out).size == (pic.WIDTH, pic.HEIGHT)


def test_bubble_colours_follow_status_in_both_weeks(tmp_path):
    # expected 7h: 5h under (blue), 7h optimal (green), 9h over (red), 0h grey
    out = pic.render_row("Anyone", 7, both([5, 7, 9, 0, 0], [9, 5, 7, 0, 0]), str(tmp_path / "row.png"))
    im = Image.open(out).convert("RGB")
    for group, hours in ((0, [5, 7, 9]), (1, [9, 5, 7])):
        for i, h in enumerate(hours):
            colour = pic.COLORS["under" if h < 7 else "optimal" if h == 7 else "over"]
            assert near(centre_pixel(im, group, i, h, 7), colour), f"group {group} slot {i} ({h}h)"
    assert near(im.getpixel((round(pic.slot_x(0, 3)), pic.CENTRE_Y)), pic.COLORS["none"])


def test_a_single_week_still_works(tmp_path):
    out = pic.render_row("X", 7, {"This week": week(7, 7, 7, 7, 7)}, str(tmp_path / "one.png"))
    assert Image.open(out).size == (pic.WIDTH, pic.HEIGHT)


def test_bigger_workload_means_bigger_bubble():
    assert pic.diameter(3, 7) < pic.diameter(7, 7) < pic.diameter(10, 7) <= pic.MAX_D < pic.HEIGHT
    assert pic.diameter(0, 7) == 0


def test_zero_or_missing_expected_hours_does_not_crash(tmp_path):
    pic.render_row("X", 0, both([2, 0, 0, 0, 0], [0] * 5), str(tmp_path / "a.png"))
    pic.render_row("X", None, both([2, 0, 0, 0, 0], [0] * 5), str(tmp_path / "b.png"))


def test_odd_names_do_not_crash(tmp_path):
    pic.render_row("Nguyễn Thị $x$ & <b> " + "n" * 80, 7, both([1] * 5, [1] * 5), str(tmp_path / "c.png"))
