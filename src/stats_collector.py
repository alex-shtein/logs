from __future__ import annotations

import os
from collections import defaultdict
from dataclasses import dataclass
from dataclasses import field
from math import floor
from typing import Dict
from typing import List
from typing import Set


@dataclass
class ResponseSizeInBytes:
    average: float  # с точностью до 2 знаков
    max: float  # с точностью до 2 знаков
    p95: float  # с точностью до 2 знаков


@dataclass
class ResourceStat:
    resource: str
    totalRequestsCount: int


@dataclass
class ResponseCodeStat:
    code: int
    totalResponsesCount: int


@dataclass
class RequestPerDateStat:
    date: str
    weekday: str
    totalRequestsCount: int
    totalRequestsPercentage: float  # округлено до 2 знаков


@dataclass
class StatsResult:
    files: List[str]
    totalRequestsCount: int
    responseSizeInBytes: ResponseSizeInBytes
    resources: List[ResourceStat]
    responseCodes: List[ResponseCodeStat]
    requestsPerDate: List[RequestPerDateStat] = field(default_factory=list)
    uniqueProtocols: List[str] = field(default_factory=list)


class StatsCollector:
    def __init__(self, files: List[str]) -> None:
        self._raw_files: List[str] = list(files)  # исходные пути
        self.total_requests: int = 0
        self.sum_sizes: int = 0
        self.max_size: int = 0
        self.sizes: List[int] = []  # для p95

        self.by_status: Dict[int, int] = defaultdict(int)
        self.by_resource: Dict[str, int] = defaultdict(int)
        self.by_date: Dict[str, int] = defaultdict(int)
        self.weekday_by_date: Dict[str, str] = {}
        self.protocols: Set[str] = set()

    def update(self, entry) -> None:
        self.total_requests += 1

        s = int(entry.response_size)
        self.sum_sizes += s
        if s > self.max_size:
            self.max_size = s
        self.sizes.append(s)

        self.by_status[int(entry.status_code)] += 1
        self.by_resource[str(entry.resource)] += 1
        self.by_date[str(entry.date_str)] += 1

        if entry.date_str not in self.weekday_by_date:
            self.weekday_by_date[entry.date_str] = entry.weekday

        if entry.protocol:
            self.protocols.add(str(entry.protocol))

    # --- P95: Hyndman & Fan "Type 7" (как в NumPy по умолчанию) ---
    def _p95(self) -> float:
        if not self.sizes:
            return 0.0
        x = sorted(self.sizes)
        n = len(x)
        p = 0.95
        # h = 1 + (n - 1) * p
        h = 1 + (n - 1) * p
        j = int(floor(h))  # база 1
        g = h - j
        # индексы переводим в 0-базу
        j0 = max(1, min(j, n)) - 1
        if j >= n:
            val = float(x[-1])
        else:
            val = x[j0] + g * (x[j0 + 1] - x[j0])
        return round(float(val), 2)

    def _format_files(self) -> List[str]:
        """Только имена файлов + стабильная сортировка лексикографически."""
        names = [os.path.basename(p) for p in self._raw_files]
        return sorted(names)

    def _sort_protocols(self) -> List[str]:
        """
        Порядок как в примере:
        - HTTP/1.* (по убыванию минорной версии),
        - затем HTTP/2.* (по убыванию минорной),
        - затем остальные (лексикографически).
        """

        def key(p: str):
            if p.startswith("HTTP/"):
                try:
                    ver = p.split("/", 1)[1]
                    major_str, minor_str = ver.split(".", 1)
                    major = int(major_str)
                    minor = int(minor_str)
                except Exception:
                    # странный формат — отправим в конец
                    return (3, p)
                if major == 1:
                    return (0, -minor)  # 1.1 перед 1.0
                if major == 2:
                    return (1, -minor)
                return (2, major, -minor)
            return (3, p)

        return sorted(self.protocols, key=key)

    def build_result(self) -> StatsResult:
        # размеры ответа
        if self.total_requests == 0:
            sizes = ResponseSizeInBytes(average=0.0, max=0.0, p95=0.0)
        else:
            avg = round(self.sum_sizes / self.total_requests, 2)
            mx = round(float(self.max_size), 2)
            p95 = self._p95()
            sizes = ResponseSizeInBytes(average=avg, max=mx, p95=p95)

        # топ-10 ресурсов (по убыванию счётчика; при равенстве — по ресурсу)
        resources_sorted = sorted(
            self.by_resource.items(), key=lambda kv: (-kv[1], kv[0])
        )
        top10 = [ResourceStat(r, c) for r, c in resources_sorted[:10]]

        # коды ответа: по убыванию количества, при равенстве — по коду
        codes = [
            ResponseCodeStat(code, cnt)
            for code, cnt in sorted(
                self.by_status.items(), key=lambda kv: (-kv[1], kv[0])
            )
        ]

        # распределение по датам
        per_date: List[RequestPerDateStat] = []
        if self.total_requests > 0:
            for d in sorted(self.by_date.keys()):
                cnt = self.by_date[d]
                pct = round(cnt * 100.0 / self.total_requests, 2)
                per_date.append(
                    RequestPerDateStat(
                        date=d,
                        weekday=self.weekday_by_date.get(d, ""),
                        totalRequestsCount=cnt,
                        totalRequestsPercentage=pct,
                    )
                )

        return StatsResult(
            files=self._format_files(),
            totalRequestsCount=self.total_requests,
            responseSizeInBytes=sizes,
            resources=top10,
            responseCodes=codes,
            requestsPerDate=per_date,
            uniqueProtocols=self._sort_protocols(),
        )
