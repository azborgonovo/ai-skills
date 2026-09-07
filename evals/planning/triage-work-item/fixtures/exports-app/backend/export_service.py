"""Builds the order export that GET /api/exports returns."""

SUPPORTED_FORMATS = ("pdf",)
QUERY_TIMEOUT_SECONDS = 30


def build_export(db, tenant_id, fmt="pdf"):
    if fmt not in SUPPORTED_FORMATS:
        raise ValueError(f"unsupported export format: {fmt}")
    rows = db.query(
        "SELECT * FROM orders WHERE tenant_id = %s ORDER BY created_at",
        tenant_id,
        timeout=QUERY_TIMEOUT_SECONDS,
    )
    return render_pdf(list(rows))


def render_pdf(rows):
    lines = [f"{r['id']},{r['created_at']},{r['total']}" for r in rows]
    return b"%PDF-1.4\n" + "\n".join(lines).encode()
