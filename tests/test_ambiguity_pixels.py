"""CPU pixel controls distinguish visible evidence from semantic grouping."""

# ruff: noqa: ANN001, ANN201 - pytest fixtures and image geometry.
import math

import pytest
from bench import ambiguity_pixels as pixels
from PIL import Image, ImageDraw

import pylopdf

BOXES = [[10, 10, 190, 30], [10, 70, 190, 90]]
BBOX = [0, 0, 200, 100]


def descriptor(image):
    return pixels.analyze(image, BOXES, image_bbox=BBOX, font_scale=20)


def test_whitespace_gap_never_establishes_grouping():
    image = Image.new("RGB", (200, 100), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 15, 50, 25), fill="black")
    draw.rectangle((20, 75, 50, 85), fill="black")
    result = descriptor(image)
    assert result["features"]["horizontal_whitespace_valley"] == 1
    assert result["features"]["valley_contrast"] > 0
    assert result["features"]["thin_horizontal_rule_count"] == 0
    assert result["qualifiers"]["choice"] == "unresolved"
    assert result["qualifiers"]["supports"] == {"join": [], "split": []}


def test_rule_and_vertical_crossings_are_explicit_not_cell_identity():
    image = Image.new("RGB", (200, 100), "white")
    draw = ImageDraw.Draw(image)
    draw.line((10, 50, 189, 50), fill="black", width=1)
    draw.line((10, 0, 10, 99), fill="black", width=1)
    draw.line((189, 0, 189, 99), fill="black", width=1)
    result = descriptor(image)
    assert result["features"]["thin_horizontal_rule_count"] == 1
    assert result["features"]["vertical_crossing_count"] == 2
    assert "thin_horizontal_dark_separator" in result["qualifiers"]["visible_boundary_support"]
    assert result["qualifiers"]["choice"] == "unresolved"


def test_broad_color_edge_and_continuity():
    image = Image.new("RGB", (200, 100), (220, 240, 250))
    ImageDraw.Draw(image).rectangle((0, 50, 199, 99), fill=(250, 210, 210))
    changed = descriptor(image)
    assert changed["features"]["broad_color_transition"]
    assert changed["features"]["broad_color_delta"] == 40
    constant = descriptor(Image.new("RGB", (200, 100), (220, 240, 250)))
    assert not constant["features"]["broad_color_transition"]
    assert constant["qualifiers"]["choice"] == "unresolved"


def test_thick_dark_fill_is_not_a_thin_rule():
    image = Image.new("RGB", (200, 100), "white")
    ImageDraw.Draw(image).rectangle((10, 40, 189, 60), fill="black")
    result = descriptor(image)
    assert result["features"]["thin_horizontal_rule_count"] == 0


def test_crop_contact_and_scale_unknown_are_qualified():
    image = Image.new("RGBA", (200, 100), (0, 0, 0, 0))
    ImageDraw.Draw(image).line((0, 0, 199, 0), fill=(0, 0, 0, 255))
    result = pixels.analyze(image, BOXES, image_bbox=BBOX)
    assert result["features"]["normalization_source"] == "selector_height"
    assert "dark_border_contact_possible_clipped_object" in result["qualifiers"]["insufficiency"]
    assert result["features"]["horizontal_whitespace_valley"] == 1


def test_small_scale_and_overlapping_selectors_abstain():
    result = pixels.analyze(
        Image.new("RGB", (200, 100), "white"), [[10, 10, 190, 55], [10, 45, 190, 90]], image_bbox=BBOX, font_scale=2
    )
    assert "small_scale_aliasing" in result["qualifiers"]["insufficiency"]
    assert "overlapping_target_boxes" in result["qualifiers"]["insufficiency"]


@pytest.mark.parametrize("font", [math.nan, math.inf, -1, 0, True])
def test_nonfinite_or_invalid_scale_refused(font):
    with pytest.raises(ValueError, match="Font scale"):
        pixels.analyze(Image.new("RGB", (200, 100)), BOXES, image_bbox=BBOX, font_scale=font)


def test_bounds_and_protected_source_refused(tmp_path):
    with pytest.raises(ValueError, match="admission"):
        descriptor(Image.new("RGB", (1025, 1025)))
    with pytest.raises(ValueError, match="inside"):
        pixels.analyze(Image.new("RGB", (200, 100)), BOXES, image_bbox=[20, 0, 200, 100])
    with pytest.raises(ValueError, match="Protected"):
        pixels.extract(tmp_path / "heldout-silver" / "source.pdf", BOXES)


def test_inline_character_candidate_is_explicitly_unavailable():
    result = pixels.analyze(
        Image.new("RGB", (200, 100), "white"), [[10, 20, 60, 40], [70, 20, 190, 40]], image_bbox=BBOX
    )
    assert not result["features"]["available"]
    assert result["qualifiers"]["choice"] == "unresolved"
    assert result["scope"]["boundary_corridor"] is None


def test_fresh_pdf_crop_keeps_exact_display_coverage(tmp_path):
    path = tmp_path / "source.pdf"
    with pylopdf.Document() as document:
        page = document.new_page(width=200, height=100)
        page.insert_text((20, 25), "Upper")
        page.insert_text((20, 85), "Lower")
        document.save(path)
    result = pixels.extract(path, BOXES, scope_bbox=[0.3, 0.4, 199.7, 99.6], font_scale=20)
    assert result["scope"]["page_index"] == 0
    assert result["scope"]["render_scale"] > 0
    assert result["scope"]["image_bbox"][0] <= 0.3
    assert result["scope"]["image_bbox"][2] >= 199.7
    assert result["features"]["available"]
    assert result["qualifiers"]["choice"] == "unresolved"
    assert len(result["provenance"]["source_sha256"]) == 64
