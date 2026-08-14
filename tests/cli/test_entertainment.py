from pathlib import Path

from tests.cli.conftest import invoke


def test_entertainment_add_and_status(runner):
    invoke(runner, ["entertainment", "topic", "add", "physics", "--name", "Physics"])
    created = invoke(
        runner,
        [
            "entertainment",
            "add",
            "Interstellar",
            "--kind",
            "film",
            "--creator",
            "Christopher Nolan",
            "--topic",
            "physics",
            "--recommended-by",
            "Alex",
        ],
    )
    assert "interstellar" in created.output

    status = invoke(
        runner,
        ["entertainment", "status", "interstellar", "--status", "done"],
    )
    assert "done" in status.output

    exported = invoke(runner, ["export"])
    assert "interstellar" in exported.output
    assert "physics" in exported.output
    assert '"entries": []' in exported.output or '"entries":[]' in exported.output


def test_entertainment_add_image_file(runner, tmp_path: Path):
    poster = tmp_path / "cover.png"
    poster.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    invoke(runner, ["entertainment", "add", "Clip", "--kind", "video", "--image", str(poster)])
    exported = invoke(runner, ["export"])
    assert "clip" in exported.output
    assert "image_base64" in exported.output
