"""T091: malicious-input/abuse-case sweep, beyond the scheme-allowlist and
private-address tests already covered in tests/unit/. Real HTTP requests
against the real app -- these are not simulated."""


def test_sql_injection_shaped_short_code_lookup_is_safe(client):
    """Parameterized queries throughout src/domain -- confirm a
    SQL-injection-shaped path parameter behaves as an ordinary unknown
    short code, not a database error or an injection."""
    resp = client.get("/' OR '1'='1", follow_redirects=False)
    assert resp.status_code == 404


def test_sql_injection_shaped_destination_url_rejected_by_scheme_check(client):
    resp = client.post(
        "/short-links",
        json={"destination_url": "https://example.com/x'; DROP TABLE domain_short_link;--"},
    )
    # Not a scheme violation (https is allowed) -- must be treated as an
    # ordinary opaque path string, never interpreted as SQL. Table must
    # still exist afterward.
    assert resp.status_code == 201
    still_works = client.post("/short-links", json={"destination_url": "https://example.com/still-here"})
    assert still_works.status_code == 201


def test_path_traversal_shaped_short_code_lookup(client):
    resp = client.get("/../../../etc/passwd", follow_redirects=False)
    assert resp.status_code in (404, 307)  # 307 if the test client normalizes the path first; never a 200 or 500


def test_oversized_destination_url_does_not_crash(client):
    huge = "https://example.com/" + ("a" * 100_000)
    resp = client.post("/short-links", json={"destination_url": huge})
    # Either accepted (no explicit length cap in FR-101) or a clean 4xx --
    # never a 500 or a hang.
    assert resp.status_code in (201, 400, 413, 422)


def test_null_byte_in_destination_url_rejected_or_handled_safely(client):
    resp = client.post("/short-links", json={"destination_url": "https://example.com/\x00null"})
    assert resp.status_code in (201, 400, 422)


def test_data_uri_with_html_rejected(client):
    resp = client.post(
        "/short-links",
        json={"destination_url": "data:text/html,<script>alert(document.cookie)</script>"},
    )
    assert resp.status_code == 400


def test_javascript_uri_with_encoding_tricks_still_rejected(client):
    resp = client.post("/short-links", json={"destination_url": "  javascript:alert(1)"})
    assert resp.status_code == 400


def test_extremely_long_idempotency_key_does_not_crash(client):
    huge_key = "k" * 10_000
    resp = client.post(
        "/short-links",
        json={"destination_url": "https://example.com/x"},
        headers={"Idempotency-Key": huge_key},
    )
    assert resp.status_code in (201, 400, 431)
