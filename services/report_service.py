_reports: dict = {}


def register_report(report_id: str, status: str, detail: str = ""):
    if status == "OK":
        _reports[report_id] = {"status": "OK", "detail": ""}
    else:
        _reports[report_id] = {"status": "ERROR", "detail": detail}


def get_reports() -> dict:
    return _reports.copy()


def clear_reports():
    _reports.clear()


def generate_ia_report() -> str:
    if not _reports:
        return ""
    
    def get_timestamp(report_id: str) -> str:
        parts = report_id.rsplit('_', 1)
        if len(parts) == 2 and parts[1].isdigit():
            return parts[1]
        return '0'
    
    sorted_reports = sorted(
        _reports.items(),
        key=lambda x: get_timestamp(x[0])
    )
    
    lines = [">>> IA REPORT - LÍNEA DE TIEMPO DE SESIÓN <<<"]
    
    for report_id, data in sorted_reports:
        if data["status"] == "OK":
            lines.append(f"[OK] {report_id}")
        else:
            lines.append(f"[ERROR] {report_id}: {data['detail']}")
    
    lines.append("\n⚠️ IMPORTANTE: Solo los IDs con [OK] existen en el código actual.")
    
    return "\n".join(lines)
