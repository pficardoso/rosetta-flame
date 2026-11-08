from rosetta_flame import __version__
from rosetta_flame.cli import main


def test_version_is_set():
    assert __version__


def test_main_runs(capsys):
    assert main([]) == 0
    assert "ready" in capsys.readouterr().out
