
import pytest

from app.cli import main as cli


def test_show_menu_displays_all_companies(capsys):
    cli.show_menu()

    output = capsys.readouterr().out

    for company in cli.COMPANIES:
        assert company["name"] in output

    assert "7) All of the above" in output
    assert "0) Quit" in output


@pytest.mark.parametrize(
    "choice, expected_index",
    [
        ("1", 0),
        ("2", 1),
        ("3", 2),
        ("4", 3),
        ("5", 4),
        ("6", 5),
    ],
)
def test_choose_individual_company(choice, expected_index):
    result = cli.choose_companies(choice)

    assert result == [cli.COMPANIES[expected_index]]


@pytest.mark.parametrize("choice", ["7", "all", "ALL", "a", "A"])
def test_choose_all_companies(choice):
    result = cli.choose_companies(choice)

    assert result == cli.COMPANIES
    assert len(result) == 6


@pytest.mark.parametrize(
    "choice",
    ["", "0", "8", "abc", "-1", "1.5"],
)
def test_choose_companies_rejects_invalid_input(choice):
    assert cli.choose_companies(choice) is None


def test_choose_companies_accepts_whitespace():
    result = cli.choose_companies("  1  ")

    assert result == [cli.COMPANIES[0]]



from unittest.mock import MagicMock, patch


def test_process_company_calls_services_in_order():
    session = MagicMock()
    company = cli.COMPANIES[0]

    filing = {
        "company": "Apple",
        "filing_date": "2026-10-30",
        "report_date": "2026-09-30",
    }

    with (
        patch.object(cli, "find_latest_10k", return_value=filing) as find,
        patch.object(cli, "download_html", return_value="<html>Report</html>") as download,
        patch.object(
            cli,
            "save_filing_files",
            return_value={"pdf_path": "downloads/Apple/report.pdf"},
        ) as save,
    ):
        result = cli.process_company(session, company)

    assert result == "downloads/Apple/report.pdf"
    find.assert_called_once_with(session, company["cik"])
    download.assert_called_once_with(session, filing)
    save.assert_called_once_with(filing, "<html>Report</html>")


def test_process_company_propagates_errors():
    session = MagicMock()
    company = cli.COMPANIES[0]

    with patch.object(
        cli,
        "find_latest_10k",
        side_effect=RuntimeError("SEC unavailable"),
    ):
        with pytest.raises(RuntimeError, match="SEC unavailable"):
            cli.process_company(session, company)


def test_run_processes_all_companies_successfully(capsys):
    selected = cli.COMPANIES
    session = MagicMock()

    with patch.object(
        cli,
        "process_company",
        side_effect=[f"report_{i}.pdf" for i in range(6)],
    ) as process:
        cli.run(selected, session)

    assert process.call_count == 6

    output = capsys.readouterr().out
    assert "Done. 6 saved, 0 failed." in output


def test_run_continues_when_one_company_fails(capsys):
    selected = cli.COMPANIES[:3]
    session = MagicMock()

    with patch.object(
        cli,
        "process_company",
        side_effect=[
            "apple.pdf",
            RuntimeError("SEC unavailable"),
            "alphabet.pdf",
        ],
    ) as process:
        cli.run(selected, session)

    assert process.call_count == 3

    output = capsys.readouterr().out
    assert "Done. 2 saved, 1 failed." in output
    assert "Failed: Meta" in output
    assert "SEC unavailable" in output


def test_main_with_single_company(monkeypatch):
    session = MagicMock()
    monkeypatch.setattr("sys.argv", ["cli", "--company", "1"])

    with (
        patch.object(cli, "make_session", return_value=session),
        patch.object(cli, "run") as run,
    ):
        cli.main()

    run.assert_called_once_with([cli.COMPANIES[0]], session)


def test_main_with_all_companies(monkeypatch):
    session = MagicMock()
    monkeypatch.setattr("sys.argv", ["cli", "--company", "all"])

    with (
        patch.object(cli, "make_session", return_value=session),
        patch.object(cli, "run") as run,
    ):
        cli.main()

    run.assert_called_once_with(cli.COMPANIES, session)


def test_main_rejects_invalid_company(monkeypatch):
    monkeypatch.setattr("sys.argv", ["cli", "--company", "99"])

    with patch.object(cli, "make_session"):
        with pytest.raises(SystemExit) as exc:
            cli.main()

    assert str(exc.value) == "Invalid company. Use 1-6, 7, or 'all'."


def test_main_overrides_user_agent(monkeypatch):
    session = MagicMock()
    session.headers = {}

    monkeypatch.setattr(
        "sys.argv",
        ["cli", "--company", "1", "--user-agent", "MyApp contact@example.com"],
    )

    with (
        patch.object(cli, "make_session", return_value=session),
        patch.object(cli, "run"),
    ):
        cli.main()

    assert session.headers["User-Agent"] == "MyApp contact@example.com"


def test_main_interactive_quit(monkeypatch, capsys):
    session = MagicMock()
    monkeypatch.setattr("sys.argv", ["cli"])
    monkeypatch.setattr("builtins.input", lambda _: "0")

    with patch.object(cli, "make_session", return_value=session):
        cli.main()

    output = capsys.readouterr().out
    assert "Goodbye." in output


def test_main_interactive_invalid_choice_then_quit(monkeypatch, capsys):
    session = MagicMock()
    answers = iter(["invalid", "0"])

    monkeypatch.setattr("sys.argv", ["cli"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    with patch.object(cli, "make_session", return_value=session):
        cli.main()

    output = capsys.readouterr().out
    assert "Please enter a valid menu option." in output
    assert "Goodbye." in output


def test_main_interactive_valid_choice(monkeypatch):
    session = MagicMock()
    answers = iter(["1", "0"])

    monkeypatch.setattr("sys.argv", ["cli"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))

    with (
        patch.object(cli, "make_session", return_value=session),
        patch.object(cli, "run") as run,
    ):
        cli.main()

    run.assert_called_once_with([cli.COMPANIES[0]], session)


def test_script_entry_point_calls_main(monkeypatch):
    import runpy

    monkeypatch.setattr("sys.argv", ["app.cli.main"])

    with (
        patch("app.services.filing_service.make_session") as make_session,
        patch("builtins.input", return_value="0"),
    ):
        runpy.run_module("app.cli.main", run_name="__main__")

    make_session.assert_called_once()
