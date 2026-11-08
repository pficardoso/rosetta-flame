from rosetta_flame import __version__
from rosetta_flame.cli import main


def test_version_is_set():
    assert __version__


def test_main_runs(capsys):
    assert main([]) == 0
    assert "ready" in capsys.readouterr().out


def test_seed_topics_imports_then_reports_unchanged(tmp_path, capsys):
    db = str(tmp_path / "test.db")
    assert main(["--db", db, "seed", "topics"]) == 0
    assert "176 created, 0 updated, 0 unchanged." in capsys.readouterr().out
    assert main(["--db", db, "seed", "topics"]) == 0
    assert "0 created, 0 updated, 176 unchanged." in capsys.readouterr().out


def test_seed_topics_dry_run_writes_nothing(tmp_path, capsys):
    db = str(tmp_path / "test.db")
    assert main(["--db", db, "seed", "topics", "--dry-run"]) == 0
    assert "176 created" in capsys.readouterr().out
    assert main(["--db", db, "seed", "topics", "--dry-run"]) == 0
    assert "176 created" in capsys.readouterr().out
