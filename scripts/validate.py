#!/usr/bin/env python3
"""Check provenance, reference integrity, counts and full-text admission rules."""
import csv
from collections import Counter
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parents[1]


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def main():
    entries = load("data/discoveries/antiwarsongs.json")
    versions = load("data/versions.json")
    sources = load("data/sources.json")
    snapshot = load("data/discoveries/antiwarsongs.snapshot.json")
    stats = load("data/stats.json")
    ids = [r["id"] for r in entries]
    vids = [v["id"] for v in versions]
    assert len(ids) == len(set(ids)), "Duplicate discovery IDs"
    assert len(vids) == len(set(vids)), "Duplicate version IDs"
    assert len(entries) == snapshot["source_entries"] == stats["source_entries"]
    assert sum(r["lyric_blocks_at_source"] for r in entries) == snapshot["lyric_blocks"]
    assert sum(r["has_lyrics_at_source"] for r in entries) == snapshot["entries_with_lyrics"] == stats["entries_with_lyrics_at_source"]
    assert stats["supporting_entries"] + stats["entries_with_lyrics_at_source"] == len(entries)
    assert stats["independent_version_total"] is None, "Do not publish unreviewed entries as independent versions"
    source_ids = {s["id"] for s in sources}
    assert len(source_ids) == len(sources), "Duplicate source IDs"
    for r in entries:
        assert r["source_id"] in source_ids
        assert urlparse(r["source_url"]).fragment == r["source_anchor"]
        assert set(r["canonical_version_ids"]) <= set(vids), f"Dangling version reference: {r['id']}"
        assert r["has_lyrics_at_source"] == bool(r["lyric_blocks_at_source"])
        assert r["heading_metadata_only"] and len(" ".join(r["heading_as_reported"])) <= 650
        assert r["local_lyrics_path"] is None, "Unreviewed AWS source texts must not masquerade as local full texts"
    book_entries = load("data/discoveries/song-yiwei-2022.json")
    book_snapshot = load("data/discoveries/song-yiwei-2022.snapshot.json")
    book_ids = [r["id"] for r in book_entries]
    assert len(book_ids) == len(set(book_ids)) == book_snapshot["source_entries"] == 44
    assert not set(book_ids) & set(ids), "Discovery IDs collide across sources"
    assert [r["book_entry"] for r in book_entries] == [f"1.{n}" for n in range(1, 34)] + [f"2.{n}" for n in range(1, 12)]
    assert sum(r["section"] == 1 for r in book_entries) == book_snapshot["chinese_publication_entries"] == 33
    assert sum(r["section"] == 2 for r in book_entries) == book_snapshot["foreign_source_entries"] == 11
    assert dict(Counter(r["language_code"] for r in book_entries if r["section"] == 2)) == book_snapshot["foreign_entries_by_language"]
    assert book_snapshot["independent_version_total"] is None and book_snapshot["local_full_texts_added"] == 0
    assert not book_snapshot["source_pdf_distributed"]
    assert re.fullmatch(r"[0-9a-f]{64}", book_snapshot["source_pdf_sha256"])
    assert book_snapshot["source_pdf_pages"] == 397 and book_snapshot["source_pdf_bytes"] == 51752151
    offset = book_snapshot["page_mapping"]["pdf_page_offset"]
    assert offset == 17
    for pair in book_snapshot["page_mapping"]["visually_checked_pairs"]:
        assert pair["pdf_page"] == pair["book_page"] + offset
    reviewed = []
    for r in book_entries:
        assert r["source_id"] == book_snapshot["source_id"] and r["source_id"] in source_ids
        assert r["pdf_page_start"] == r["book_page_start"] + offset
        assert 1 <= r["pdf_page_start"] <= book_snapshot["source_pdf_pages"]
        assert r["review_status"] == "toc-reviewed"
        assert r["header_review_status"] in {"visually-reviewed", "pending"}
        assert bool(r["reported_provenance"]) == (r["header_review_status"] == "visually-reviewed")
        if r["header_review_status"] == "visually-reviewed":
            reviewed.append(r["book_entry"])
        for p in r["reported_provenance"]:
            assert p["citation"] and p["kind"].endswith("-reported")
            assert p["evidence_book_page"] == r["book_page_start"]
            assert p["evidence_pdf_page"] == r["pdf_page_start"]
        assert set(r["related_version_ids"] + r["canonical_version_ids"]) <= set(vids)
        assert r["local_lyrics_path"] is None and r["rights_status"] == "unassessed"
        assert r["facsimile_collation"] == "pending"
    assert reviewed == book_snapshot["visually_reviewed_header_entries"]
    from build_book_catalogue import render as render_book_catalogue
    assert (ROOT / "catalogue/book-song-2022.md").read_text(encoding="utf-8") == render_book_catalogue(book_entries), "Stale book catalogue"
    allowed = {"public-domain-supported", "open-license-verified", "permission-verified"}
    listed_files = set()
    for v in versions:
        assert v["sources"] and all(urlparse(s["url"]).scheme in {"http","https"} for s in v["sources"])
        assert len(v["stanza_mapping"]) == len(set(v["stanza_mapping"]))
        assert all(1 <= n <= 6 for n in v["stanza_mapping"])
        if not v["lyrics_path"]:
            continue
        assert v["rights"]["status"] in allowed and v["rights"]["evidence_urls"]
        p = ROOT / v["lyrics_path"]
        assert p.is_file(), f"Missing text: {p}"
        body = p.read_text(encoding="utf-8")
        assert hashlib.sha256(body.encode()).hexdigest() == v["lyrics_sha256"], f"Text changed without updating record: {p}"
        assert len(body.split("```text\n",1)[1].split("```",1)[0].strip()) > 250
        assert "{{" not in body and "<script" not in body
        listed_files.add(p.resolve())
    assert listed_files == {p.resolve() for p in (ROOT / "lyrics").rglob("*.md")}, "Unregistered lyric text"
    assert len(listed_files) == stats["local_full_texts"]
    assert len(versions) == stats["curated_records"]
    with (ROOT / "catalogue/discoveries.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert [r["id"] for r in rows] == ids
    viewer = (ROOT / "catalogue.html").read_text(encoding="utf-8")
    embedded = re.search(r'<script id="catalogue-data" type="application/json">(.*?)</script>', viewer, re.S)
    assert embedded, "Missing offline catalogue data"
    assert json.loads(embedded[1])["entries"] == entries, "Stale offline catalogue"
    # Local Markdown paths: allow parentheses inside normal link destinations.
    missing = []
    for p in ROOT.rglob("*.md"):
        for target in re.findall(r'\]\(([^)\s]+)\)', p.read_text(encoding="utf-8")):
            if urlparse(target).scheme or target.startswith("#"):
                continue
            path = unquote(target.split("#",1)[0])
            if path and not (p.parent / path).exists():
                missing.append((str(p.relative_to(ROOT)),target))
    assert not missing, f"Broken local links: {missing}"
    en = (ROOT / "lyrics/en/en-kerr-1900.md").read_text(encoding="utf-8")
    assert "(Alternate chorus)" not in en
    zh = (ROOT / "lyrics/zh/zh-qu-1923.md").read_text(encoding="utf-8")
    assert zh.count("起來，受人污辱咒罵的！") == 1 and zh.count("人類方重興！") == 6
    assert "✽✽✽" in zh
    print(f"PASS: {len(entries)} AWS discovery entries; {snapshot['lyric_blocks']} source lyric blocks accounted for; {len(book_entries)} book source entries ({len(reviewed)} headers reviewed); {len(versions)} identity records; {len(listed_files)} admitted texts; CSV, embedded catalogue, book index and local links consistent.")


if __name__ == "__main__":
    main()
