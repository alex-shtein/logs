import json
import os
from pathlib import Path

import pytest

from src.main import run
from src.exit_codes import ExitCode


# ---------- helpers ----------

VALID_LINE = (
    "93.180.71.3 - - [17/May/2015:08:05:32 +0000] "
    '"GET /downloads/product_1 HTTP/1.1" 304 0 "-" "UA"'
)


def make_log(path: Path, lines: list[str]) -> Path:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# 1 - На вход передан несуществующий локальный файл
def test_missing_local_file(tmp_path: Path):
    out = tmp_path / "report.json"
    code = run(["-p", str(tmp_path / "no_such.log"), "-f", "json", "-o", str(out)])
    assert code == ExitCode.BAD_USAGE


# 2 - На вход передан несуществующий удаленный файл (404)
def test_missing_remote_file(monkeypatch, tmp_path: Path):
    class FakeResp:
        status_code = 404

    import requests
    monkeypatch.setattr(requests, "head", lambda *a, **kw: FakeResp())
    out = tmp_path / "report.json"
    code = run(["-p", "http://example.com/missing.log", "-f", "json", "-o", str(out)])
    assert code == ExitCode.BAD_USAGE


# 3 - На вход передан файл в неподдерживаемом формате
def test_unsupported_input_extension(tmp_path: Path):
    bad = tmp_path / "input.csv"
    bad.write_text("hello\n", encoding="utf-8")
    out = tmp_path / "report.json"
    code = run(["-p", str(bad), "-f", "json", "-o", str(out)])
    assert code == ExitCode.BAD_USAGE


# 4 - Невалидные параметры --from / --to
@pytest.mark.parametrize(
    "from_val,to_val",
    [
        ("2025.01.01 10:30", None),  # неверный формат
        (None, "today"),  # неверный формат
    ],
)
def test_invalid_from_to_formats(tmp_path: Path, from_val, to_val):
    logf = make_log(tmp_path / "a.log", [VALID_LINE])
    out = tmp_path / "report.json"
    argv = ["-p", str(logf), "-f", "json", "-o", str(out)]
    if from_val is not None:
        argv += ["--from", from_val]
    if to_val is not None:
        argv += ["--to", to_val]
    code = run(argv)
    assert code == ExitCode.BAD_USAGE


# 5 - Результаты запрошены в неподдерживаемом формате: txt
def test_unsupported_output_format(tmp_path: Path):
    logf = make_log(tmp_path / "a.log", [VALID_LINE])
    out = tmp_path / "report.txt"
    code = run(["-p", str(logf), "-f", "txt", "-o", str(out)])
    assert code == ExitCode.BAD_USAGE


# 6 - По пути --output указан файл с некорректным расширением
def test_output_extension_mismatch(tmp_path: Path):
    logf = make_log(tmp_path / "a.log", [VALID_LINE])
    out = tmp_path / "report.md"  # но формат json
    code = run(["-p", str(logf), "-f", "json", "-o", str(out)])
    assert code == ExitCode.BAD_USAGE


# 7 - По пути --output уже существует файл
def test_output_already_exists(tmp_path: Path):
    logf = make_log(tmp_path / "a.log", [VALID_LINE])
    out = tmp_path / "report.json"
    out.write_text("exists", encoding="utf-8")
    code = run(["-p", str(logf), "-f", "json", "-o", str(out)])
    assert code == ExitCode.BAD_USAGE


# 8 - Не передан обязательный параметр: "--path", "--output", "--format", "-p", "-o", "-f"
@pytest.mark.parametrize(
    "argv",
    [
        # отсутствует --path/-p
        ["-f", "json", "-o", "report.json"],
        # отсутствует --output/-o
        ["-p", "x.log", "-f", "json"],
        # отсутствует --format/-f
        ["-p", "x.log", "-o", "report.json"],
    ],
)
def test_missing_required_arguments(argv):
    code = run(argv)
    assert code == ExitCode.BAD_USAGE


# 9 - Неподдерживаемый параметр: "--input", "--filter"
@pytest.mark.parametrize("extra", [["--input"], ["--filter"]])
def test_unknown_argument(extra, tmp_path: Path):
    logf = make_log(tmp_path / "a.log", [VALID_LINE])
    out = tmp_path / "report.json"
    argv = ["-p", str(logf), "-f", "json", "-o", str(out)] + extra
    code = run(argv)
    assert code == ExitCode.BAD_USAGE


# 10 - Значение --from больше, чем --to
def test_from_greater_than_to(tmp_path: Path):
    logf = make_log(tmp_path / "a.log", [VALID_LINE])
    out = tmp_path / "report.json"
    code = run(
        [
            "-p",
            str(logf),
            "-f",
            "json",
            "-o",
            str(out),
            "--from",
            "2025-01-02",
            "--to",
            "2025-01-01",
        ]
    )
    assert code == ExitCode.BAD_USAGE
