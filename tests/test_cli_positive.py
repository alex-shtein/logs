import json
from pathlib import Path
import pytest

from src.main import run
from src.exit_codes import ExitCode


VALID_1 = (
    "93.180.71.3 - - [17/May/2015:08:05:23 +0000] "
    '"GET /downloads/product_1 HTTP/1.1" 304 0 "-" "UA"'
)
VALID_2 = (
    "93.180.71.3 - - [17/May/2015:08:05:32 +0000] "
    '"GET /downloads/product_2 HTTP/1.0" 200 100 "-" "UA"'
)
VALID_OLD_DAY = (
    "93.180.71.3 - - [01/May/2015:12:00:00 +0000] "
    '"GET /downloads/product_2 HTTP/2.1" 404 50 "-" "UA"'
)
INVALID_LINE = "this is not nginx line"


def make_log(path: Path, lines: list[str]) -> Path:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# 11 - Валидный локальный log-файл (smoke, exit 0)
def test_local_log_smoke_ok(tmp_path: Path):
    logf = make_log(tmp_path / "ok.log", [VALID_1, VALID_2])
    out = tmp_path / "report.json"
    code = run(["-p", str(logf), "-f", "json", "-o", str(out)])
    assert code == ExitCode.OK
    assert out.exists()


# 12 - Валидный удаленный log-файл (моки сети)
def test_remote_log_smoke_ok(monkeypatch, tmp_path: Path):
    import requests
    class HeadResp:
        status_code = 200
    monkeypatch.setattr(requests, "head", lambda *a, **kw: HeadResp())

    # GET 200 + строки
    from src.reader import reader_url
    lines = [VALID_1, VALID_2]
    class GetResp:
        status_code = 200
        def __enter__(self): return self
        def __exit__(self, *exc): return False
        def iter_lines(self, decode_unicode=True):
            for s in lines:
                yield s

    monkeypatch.setattr(reader_url.requests, "get", lambda *a, **kw: GetResp())

    out = tmp_path / "report.json"
    code = run(["-p", "http://example.com/nginx.log", "-f", "json", "-o", str(out)])
    assert code == ExitCode.OK
    assert out.exists()


# 13 - Фильтрация по --from/--to
def test_filter_by_from_to(tmp_path: Path):
    # одна строка 01/May/2015, две строки 17/May/2015
    logf = make_log(tmp_path / "flt.log", [VALID_OLD_DAY, VALID_1, VALID_2])
    out = tmp_path / "report.json"
    # берём только 17/May/2015 (включительно)
    code = run(
        [
            "-p",
            str(logf),
            "-f",
            "json",
            "-o",
            str(out),
            "--from",
            "2015-05-17",
            "--to",
            "2015-05-17",
        ]
    )
    assert code == ExitCode.OK
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["totalRequestsCount"] == 2
    # обе строки 17-го
    assert sorted([r["resource"] for r in data["resources"]]) == [
        "/downloads/product_1",
        "/downloads/product_2",
    ]


# 14 - Часть строк не подходит под формат
def test_skip_invalid_lines(tmp_path: Path):
    logf = make_log(
        tmp_path / "mix.log", [INVALID_LINE, VALID_1, INVALID_LINE, VALID_2]
    )
    out = tmp_path / "report.json"
    code = run(["-p", str(logf), "-f", "json", "-o", str(out)])
    assert code == ExitCode.OK
    data = json.loads(out.read_text(encoding="utf-8"))
    # учлись только 2 валидные строки
    assert data["totalRequestsCount"] == 2


# 15 - Расчёт статистики на локальном файле (проверка avg/max/p95, codes, top resources)
def test_stats_values(tmp_path: Path):
    # sizes: 0 (304), 100 (200), 50 (404) -> avg = 50.0, max = 100.0, p95 ~ 95.0 (Type7)
    logf = make_log(tmp_path / "stats.log", [VALID_1, VALID_2, VALID_OLD_DAY])
    out = tmp_path / "report.json"
    code = run(["-p", str(logf), "-f", "json", "-o", str(out)])
    assert code == ExitCode.OK
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["responseSizeInBytes"]["average"] == pytest.approx(50.0, abs=1e-2)
    assert data["responseSizeInBytes"]["max"] == pytest.approx(100.0, abs=1e-2)
    assert data["responseSizeInBytes"]["p95"] == pytest.approx(95.0, abs=1e-2)
    # codes sorted by count desc
    codes = data["responseCodes"]
    assert [c["code"] for c in codes] == [200, 304, 404]
    # resources top2 present
    assert len(data["resources"]) == 2


# 16 - Сохранение статистики в формате JSON
def test_output_json(tmp_path: Path):
    logf = make_log(tmp_path / "a.log", [VALID_1])
    out = tmp_path / "report.json"
    code = run(["-p", str(logf), "-f", "json", "-o", str(out)])
    assert code == ExitCode.OK
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "totalRequestsCount" in data


# 17 - Сохранение статистики в формате MARKDOWN
def test_output_markdown(tmp_path: Path):
    logf = make_log(tmp_path / "a.log", [VALID_1])
    out = tmp_path / "report.md"
    code = run(["-p", str(logf), "-f", "markdown", "-o", str(out)])
    assert code == ExitCode.OK
    text = out.read_text(encoding="utf-8")
    assert "#### Общая информация" in text


# 18 - Сохранение статистики в формате ADOC
def test_output_adoc(tmp_path: Path):
    logf = make_log(tmp_path / "a.log", [VALID_1])
    out = tmp_path / "report.ad"
    code = run(["-p", str(logf), "-f", "adoc", "-o", str(out)])
    assert code == ExitCode.OK
    text = out.read_text(encoding="utf-8")
    assert "= Отчёт по логам NGINX" in text
