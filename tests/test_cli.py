from typer.testing import CliRunner

from cmr_volume_analysis.cli import FailOn, _exit_code, app

runner = CliRunner()


def test_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.stdout


def test_exit_code_policy():
    assert _exit_code("error", FailOn.NEVER) == 0
    assert _exit_code("warning", FailOn.WARNING) == 2
    assert _exit_code("error", FailOn.ERROR) == 2
    assert _exit_code("pass", FailOn.ERROR) == 0
