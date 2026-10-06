from cli.main import CliSettings, _read_request, parse_settings


def test_cli_parses_documented_arguments():
    settings = CliSettings(
        _cli_parse_args=[
            "--host",
            "http://localhost:9000",
            "--repeat",
            "2",
            "--json",
            '{"list_1":["a"],"list_2":["b"]}',
            "--output",
            "-",
        ]
    )

    assert str(settings.host) == "http://localhost:9000/"
    assert settings.repeat == 2
    assert _read_request(settings) == {"list_1": ["a"], "list_2": ["b"]}


def test_cli_accepts_short_options_and_contextual_host_flag():
    settings = parse_settings(
        [
            "-h",
            "http://localhost:9000",
            "-r",
            "3",
            "-j",
            '{"list_1":["a"],"list_2":["b"]}',
            "-o",
            "-",
        ]
    )
    assert str(settings.host) == "http://localhost:9000/"
    assert settings.repeat == 3


def test_cli_rejects_both_input_sources():
    try:
        CliSettings(_cli_parse_args=["--input", "request.json", "--json", "{}"])
    except ValueError as exc:
        assert "either --input or --json" in str(exc)
    else:
        raise AssertionError("expected validation error")
