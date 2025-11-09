import json
from typing import Any
from typing import Dict

from src.stats_collector import StatsResult


class JsonFormatter:
    def format(self, result: StatsResult) -> str:
        payload: Dict[str, Any] = {
            "files": list(result.files),
            "totalRequestsCount": int(result.totalRequestsCount),
            "responseSizeInBytes": {
                "average": float(result.responseSizeInBytes.average),
                "max": float(result.responseSizeInBytes.max),
                "p95": float(result.responseSizeInBytes.p95),
            },
            "resources": [
                {
                    "resource": r.resource,
                    "totalRequestsCount": int(r.totalRequestsCount),
                }
                for r in result.resources
            ],
            "responseCodes": [
                {
                    "code": int(rc.code),
                    "totalResponsesCount": int(rc.totalResponsesCount),
                }
                for rc in result.responseCodes
            ],
        }

        if result.requestsPerDate:
            payload["requestsPerDate"] = [
                {
                    "date": d.date,
                    "weekday": d.weekday,
                    "totalRequestsCount": int(d.totalRequestsCount),
                    "totalRequestsPercentage": float(d.totalRequestsPercentage),
                }
                for d in result.requestsPerDate
            ]

        if result.uniqueProtocols:
            payload["uniqueProtocols"] = list(result.uniqueProtocols)

        return json.dumps(payload, ensure_ascii=False, indent=2)
