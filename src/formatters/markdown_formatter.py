from src.stats_collector import StatsResult


class MarkdownFormatter:
    def format(self, result: StatsResult) -> str:
        lines = []
        lines.append("#### Общая информация\n")
        lines.append("|        Метрика        |     Значение |")
        lines.append("|:---------------------:|-------------:|")
        files = ", ".join(f"`{f}`" for f in result.files) if result.files else "-"
        lines.append(f"|       Файл(-ы)        | {files} |")
        lines.append(f"|  Количество запросов  | {result.totalRequestsCount} |")
        lines.append(
            f"| Средний размер ответа | {result.responseSizeInBytes.average}b |"
        )
        lines.append(f"| Максимальный ответ    | {result.responseSizeInBytes.max}b |")
        lines.append(f"|   95p размера ответа  | {result.responseSizeInBytes.p95}b |")
        lines.append("")
        lines.append("#### Запрашиваемые ресурсы\n")
        lines.append("|     Ресурс      | Количество |")
        lines.append("|:---------------:|-----------:|")
        if result.resources:
            for r in result.resources:
                lines.append(f"| `{r.resource}` | {r.totalRequestsCount} |")
        else:
            lines.append("| - | 0 |")
        lines.append("")
        lines.append("#### Коды ответа\n")
        lines.append("| Код | Количество |")
        lines.append("|:---:|-----------:|")
        if result.responseCodes:
            for rc in result.responseCodes:
                lines.append(f"| {rc.code} | {rc.totalResponsesCount} |")
        else:
            lines.append("| - | 0 |")
        lines.append("")
        if result.requestsPerDate:
            lines.append("#### Запросы по датам\n")
            lines.append("|    Дата    |  День недели  | Кол-во |  % от общего |")
            lines.append("|:----------:|:-------------:|-------:|-------------:|")
            for d in result.requestsPerDate:
                lines.append(
                    f"| {d.date} | {d.weekday} | {d.totalRequestsCount} | {d.totalRequestsPercentage}% |"
                )
            lines.append("")
        if result.uniqueProtocols:
            lines.append("#### Уникальные протоколы\n")
            lines.append(", ".join(f"`{p}`" for p in result.uniqueProtocols))
            lines.append("")
        return "\n".join(lines)
