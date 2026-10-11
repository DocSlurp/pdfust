"""Preserve source transparency mathematically when inspecting black-on-alpha pages."""

from bench.p003_source_visual_check import onto_white
from PIL import Image


def test_source_alpha_is_composited_over_white_without_mutating_original() -> None:
    """Transparent pixels become white and partial black ink retains antialiasing."""
    source = Image.new("RGBA", (3, 1))
    source.putdata([(0, 0, 0, 0), (0, 0, 0, 128), (0, 0, 0, 255)])
    before = source.tobytes()
    rendered = onto_white(source)
    assert [rendered.getpixel((i, 0)) for i in range(3)] == [(255, 255, 255), (127, 127, 127), (0, 0, 0)]
    assert source.tobytes() == before
