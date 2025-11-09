from src.stats_collector import StatsResult


class AdocFormatter:
    """
    Формирует отчёт в AsciiDoc (ADOC).
    Соответствует структуре Markdown-версии, но с синтаксисом таблиц AsciiDoc.
    """

    def format(self, result: StatsResult) -> str:
        lines = []

        # Заголовок
        lines.append("= Отчёт по логам NGINX")
        lines.append("")

        # Общая информация
        lines.append("==== Общая информация")
        lines.append('[cols="2,1", options="header"]')
        lines.append("|===")
        lines.append("| Метрика | Значение")
        files = ", ".join(f"`{f}`" for f in result.files) if result.files else "-"
        lines.append(f"| Файл(-ы) | {files}")
        lines.append(f"| Количество запросов | {result.totalRequestsCount}")
        lines.append(f"| Средний размер ответа | {result.responseSizeInBytes.average}b")
        lines.append(f"| Максимальный ответ | {result.responseSizeInBytes.max}b")
        lines.append(f"| 95p размера ответа | {result.responseSizeInBytes.p95}b")
        lines.append("|===")
        lines.append("")

        # Ресурсы
        lines.append("==== Запрашиваемые ресурсы")
        lines.append('[cols="2,1", options="header"]')
        lines.append("|===")
        lines.append("| Ресурс | Количество")
        if result.resources:
            for r in result.resources:
                lines.append(f"| `{r.resource}` | {r.totalRequestsCount}")
        else:
            lines.append("| - | 0")
        lines.append("|===")
        lines.append("")

        # Коды ответа
        lines.append("==== Коды ответа")
        lines.append('[cols="1,1", options="header"]')
        lines.append("|===")
        lines.append("| Код | Количество")
        if result.responseCodes:
            for rc in result.responseCodes:
                lines.append(f"| {rc.code} | {rc.totalResponsesCount}")
        else:
            lines.append("| - | 0")
        lines.append("|===")
        lines.append("")

        # Запросы по датам (если есть)
        if result.requestsPerDate:
            lines.append("==== Запросы по датам")
            lines.append('[cols="1,1,1,1", options="header"]')
            lines.append("|===")
            lines.append("| Дата | День недели | Кол-во | % от общего")
            for d in result.requestsPerDate:
                lines.append(
                    f"| {d.date} | {d.weekday} | {d.totalRequestsCount} | {d.totalRequestsPercentage}%"
                )
            lines.append("|===")
            lines.append("")

        # Уникальные протоколы
        if result.uniqueProtocols:
            lines.append("==== Уникальные протоколы")
            lines.append(", ".join(f"`{p}`" for p in result.uniqueProtocols))
            lines.append("")

        return "\n".join(lines)
