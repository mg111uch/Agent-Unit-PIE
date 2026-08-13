import json

from vse.cli import main


def test_transformer_subcommand():
    assert (
        main(
            [
                "transformer",
                "--hidden-dim",
                "1024",
                "--heads",
                "16",
                "--layers",
                "4",
                "--intermediate",
                "2048",
                "--sequence",
                "256",
            ]
        )
        == 0
    )


def test_moe_subcommand():
    assert (
        main(
            [
                "moe",
                "--hidden-dim",
                "1024",
                "--intermediate",
                "2048",
                "--experts",
                "32",
                "--top-k",
                "2",
                "--tokens",
                "16",
            ]
        )
        == 0
    )


def test_json_output():
    output = _capture(
        [
            "transformer",
            "--hidden-dim",
            "1024",
            "--heads",
            "16",
            "--layers",
            "2",
            "--intermediate",
            "2048",
            "--sequence",
            "64",
            "--json",
        ]
    )

    result = json.loads(output)

    assert result["name"] == "transformer"
    assert result["total_cycles"] > 0


def test_search_subcommand():
    assert (
        main(
            [
                "search",
                "--model",
                "moe",
                "--hidden-dim",
                "512",
                "--intermediate",
                "1024",
                "--experts",
                "8",
                "--top-k",
                "2",
                "--tokens",
                "8",
                "--dim",
                "num_pes=128,256",
                "--dim",
                "weight_bits=4,8",
            ]
        )
        == 0
    )


def test_search_json_output():
    output = _capture(
        [
            "search",
            "--model",
            "transformer",
            "--hidden-dim",
            "256",
            "--heads",
            "4",
            "--layers",
            "2",
            "--intermediate",
            "512",
            "--sequence",
            "32",
            "--dim",
            "num_pes=256,512",
            "--json",
        ]
    )

    result = json.loads(output)

    assert result["model"] == "transformer"
    assert len(result["candidates"]) == 2
    assert result["frontier"]
    assert result["candidates"][0]["tokens_per_second"] > 0


def _capture(args):
    import io
    import sys
    from vse.cli import main as _main

    buffer = io.StringIO()
    original = sys.stdout
    sys.stdout = buffer

    try:
        _main(args)
    finally:
        sys.stdout = original

    return buffer.getvalue()
