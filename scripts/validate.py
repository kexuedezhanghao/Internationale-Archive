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
    for r in book_entries:
        verification = r.get("external_bibliographic_verification")
        if verification:
            assert urlparse(verification["url"]).scheme == "https"
            assert verification["scope"] and verification["reviewed_on"]
    from build_book_catalogue import render as render_book_catalogue
    assert (ROOT / "catalogue/book-song-2022.md").read_text(encoding="utf-8") == render_book_catalogue(book_entries), "Stale book catalogue"
    allowed = {"public-domain-supported", "open-license-verified", "permission-verified"}
    listed_files = set()
    for v in versions:
        assert v["sources"] and all(urlparse(s["url"]).scheme in {"http","https"} for s in v["sources"])
        if v.get("digital_edition_source_id"):
            assert v["digital_edition_source_id"] in source_ids
        assert set(v.get("related_version_ids", [])) <= set(vids)
        assert len(v["stanza_mapping"]) == len(set(v["stanza_mapping"]))
        assert all(1 <= n <= 6 for n in v["stanza_mapping"])
        if estimate := v.get("source_publication_year_estimate"):
            assert v["source_publication_year"] is None
            assert isinstance(estimate["year"], int) and estimate["qualifier"] == "ca"
            assert estimate["basis"] and urlparse(estimate["url"]).scheme == "https"
        for detail in v.get("stanza_mapping_details", []):
            assert 1 <= detail["printed_stanza"] <= len(v["stanza_mapping"])
            assert detail["predominant_french_stanza"] == v["stanza_mapping"][detail["printed_stanza"] - 1]
            assert detail["scope"] and detail["additional_french_stanzas"]
            assert set(detail["additional_french_stanzas"]) <= set(range(1, 7))
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
    embedded_data = json.loads(embedded[1])
    assert embedded_data == {"entries": entries, "versions": versions, "stats": stats}, "Stale offline catalogue"
    for p in (ROOT / "data/source-checks").glob("*.json"):
        check = json.loads(p.read_text(encoding="utf-8"))
        check_ids = set(check["version_ids"])
        assert len(check_ids) == len(check["version_ids"]) and check_ids <= set(vids)
        assert (ROOT / check["report_path"]).is_file()
        admitted_ids = {v["id"] for v in versions if v["id"] in check_ids and v["lyrics_path"]}
        assert admitted_ids == set(check["full_text_version_ids"])
        snapshot_urls = set()
        for page_snapshot in check["snapshots"]:
            assert urlparse(page_snapshot["url"]).scheme == "https" and page_snapshot["url"] not in snapshot_urls
            snapshot_urls.add(page_snapshot["url"])
            assert page_snapshot["snapshot_bytes"] > 0 and re.fullmatch(r"[0-9a-f]{64}", page_snapshot["snapshot_sha256"])
            assert not page_snapshot["snapshot_distributed"] and page_snapshot["encoding"]
        for part in check["serial_parts"]:
            assert part["version_id"] in check_ids and part["url"] in snapshot_urls
            assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", part["publication_date_as_reported"])
            assert part["stanza_numbers_in_web"] and set(part["stanza_numbers_in_web"]) <= set(range(1, 7))
        for conflict in check["date_conflicts"]:
            assert conflict["version_id"] in check_ids and conflict["status"]
            assert len({claim["date"] for claim in conflict["claims"]}) >= 2
            assert all(claim.get("url") or claim.get("source_id") in source_ids for claim in conflict["claims"])
        for version_id in check_ids:
            v = next(v for v in versions if v["id"] == version_id)
            assert v["review"]["source_check_record"] == str(p.relative_to(ROOT))
            assert v["review"]["source_check_report"] == check["report_path"]
            if check["facsimiles_obtained"] == 0:
                assert v["review"]["facsimile_collation"] == "pending"
        if "pdf_evidence" in check:
            pdfs = check["pdf_evidence"]
            assert sum(pdf["counts_as_facsimile"] for pdf in pdfs) == check["facsimiles_obtained"]
            for pdf in pdfs:
                assert pdf["source_id"] in source_ids and pdf["url"] in snapshot_urls
                assert pdf["pdf_bytes"] > 0 and pdf["pdf_pages"] > 0 and not pdf["pdf_distributed"]
                assert re.fullmatch(r"[0-9a-f]{64}", pdf["pdf_sha256"])
                assert re.fullmatch(r"[0-9a-f]{40}", pdf["pdf_sha1"])
                evidence = next(s for s in check["snapshots"] if s["url"] == pdf["url"])
                assert evidence["snapshot_bytes"] == pdf["pdf_bytes"]
                assert evidence["snapshot_sha256"] == pdf["pdf_sha256"]
                assert pdf["publication_locator"] and pdf["review_scope"]
                reviewed_pages = pdf["visually_reviewed_pdf_pages"]
                assert all(1 <= page <= pdf["pdf_pages"] for page in reviewed_pages)
                assert all(pair["pdf_page"] in reviewed_pages for pair in pdf["page_mapping"])
                assert len(pdf["stanza_mapping_verified"]) == len(set(pdf["stanza_mapping_verified"]))
                assert set(pdf["stanza_mapping_verified"]) <= set(range(1, 7))
            for reading in check.get("unresolved_readings", []):
                v = next(v for v in versions if v["id"] == reading["version_id"])
                assert v["id"] in check_ids and reading["id"] in v["review"]["unresolved_reading_ids"]
                assert v["review"]["facsimile_collation"] == "reviewed-with-unresolved-readings"
                assert reading["marker"] in (ROOT / v["lyrics_path"]).read_text(encoding="utf-8")
                assert reading["candidates"] and reading["status"] == "pending-review"
                assert any(pair["pdf_page"] == reading["pdf_page"] and pair["printed_page"] == reading["printed_page"]
                           for pdf in pdfs for pair in pdf["page_mapping"])
        if "image_evidence" in check:
            images = check["image_evidence"]
            assert len({im["url"] for im in images}) == len(images)
            for im in images:
                assert urlparse(im["url"]).scheme == "https"
                assert im["snapshot_bytes"] > 0 and re.fullmatch(r"[0-9a-f]{64}", im["snapshot_sha256"])
                assert im["width"] > 0 and im["height"] > 0 and not im["snapshot_distributed"]
                assert im["visually_reviewed_on"] and im["review_scope"] and im["classification"]
                if im["counts_as_facsimile"]:
                    assert im["classification"] in {"original-publication-crop", "original-publication-page"}
                    assert im["publication_locator_as_reported"]
            assert sum(im["counts_as_facsimile"] for im in images) == check["facsimiles_obtained"]
        for issue in check.get("issues", []):
            assert issue["manifest_url"] in snapshot_urls and issue["oai_url"] in snapshot_urls
            pages = [im for im in check["image_evidence"] if im.get("issue_number") == issue["issue_number"]]
            assert len(pages) == issue["downloaded_full_pages"] == issue["manifest_canvas_count"]
            assert sorted(im["printed_page"] for im in pages) == list(range(1, issue["manifest_canvas_count"] + 1))
            assert all(im["classification"] == "original-publication-page" and im["masthead_date_verified"] == issue["publication_date_verified"] for im in pages)
        for part in check.get("publication_parts", []):
            assert part["version_id"] in check_ids
            assert set(part["stanza_numbers_in_original"]) <= set(range(1, 7))
            assert any(im["issue_number"] == part["issue_number"] and im["printed_page"] == part["printed_page"] for im in check["image_evidence"])
        for difference in check.get("preliminary_differences", []):
            assert difference["facsimile"] and difference["web"] and difference["locator"]
        if "stanza_mapping_verified" in check:
            assert len(check["version_ids"]) == 1
            v = next(v for v in versions if v["id"] == check["version_ids"][0])
            assert v["stanza_mapping"] == check["stanza_mapping_verified"]
        digital = check.get("digital_edition_evidence")
        if digital:
            assert digital["source_id"] in source_ids
            assert digital["classification"] == "mixed-digital-text-and-raster-newspaper-edition"
            assert digital["pdf_bytes"] > 0 and digital["pdf_pages"] > 0
            assert re.fullmatch(r"[0-9a-f]{64}", digital["pdf_sha256"])
            assert re.fullmatch(r"[0-9a-f]{40}", digital["pdf_sha1"])
            assert 1 <= digital["pdf_page"] <= digital["pdf_pages"]
            assert digital["pdf_page"] in digital["visually_reviewed_pdf_pages"]
            assert all(1 <= page <= digital["pdf_pages"] for page in digital["visually_reviewed_pdf_pages"])
            assert digital["publication_citation"] and digital["review_scope"]
            assert not digital["pdf_distributed"] and digital["metadata_is_not_original_publication_evidence"]
            if digital["public_download_url"]:
                assert urlparse(digital["public_download_url"]).scheme == "https"
            else:
                assert digital["download_provenance_status"] == "not-established"
            raster = digital["embedded_score_raster"]
            assert raster["classification"] == "score-raster-embedded-in-digital-edition"
            assert raster["bytes"] > 0 and raster["width"] > 0 and raster["height"] > 0
            assert re.fullmatch(r"[0-9a-f]{64}", raster["sha256"])
            assert re.fullmatch(r"[0-9a-f]{40}", raster["sha1"])
            assert not raster["image_distributed"] and raster["display_transform"]
            assert all(next(v for v in versions if v["id"] == vid)["digital_edition_source_id"] == digital["source_id"] for vid in check_ids)
    for p in (ROOT / "data/collations").glob("*.json"):
        collation = json.loads(p.read_text(encoding="utf-8"))
        assert set(collation["version_ids"]) <= set(vids)
        assert (ROOT / collation["report_path"]).is_file()
        facsimile = collation["facsimile"]
        assert re.fullmatch(r"[0-9a-f]{64}", facsimile["pdf_sha256"])
        assert re.fullmatch(r"[0-9a-f]{40}", facsimile["pdf_sha1"])
        assert facsimile["pdf_bytes"] > 0 and not facsimile["scan_distributed"]
        assert all(urlparse(facsimile[k]).scheme == "https" for k in ["file_page_url", "index_url", "download_url"])
        pairs = collation["page_mapping"]["visually_checked_pairs"]
        printed_pages = {pair["printed_page"] for pair in pairs}
        assert len(printed_pages) == len(pairs)
        assert all(1 <= pair["pdf_page"] <= facsimile["pdf_pages"] for pair in pairs)
        if collation.get("record_kind") == "edition-facsimile-vs-web":
            assert collation["edition_differences"] and collation["comparison_limit"]
            for difference in collation["edition_differences"]:
                assert difference["printed_page"] in printed_pages
                assert difference["facsimile"] and difference["web"]
                assert {difference["facsimile_version_id"], difference["web_version_id"]} <= set(collation["version_ids"])
            for reading in collation["unresolved_readings"]:
                assert reading["printed_page"] in printed_pages
                assert reading["version_id"] in collation["version_ids"]
                assert reading["status"] == "pending-human-review" and reading["candidates"]
                v = next(v for v in versions if v["id"] == reading["version_id"])
                assert reading["id"] in v["review"]["unresolved_reading_ids"]
                assert v["review"]["facsimile_collation"] == "reviewed-with-unresolved-readings"
                assert reading["marker"] in (ROOT / v["lyrics_path"]).read_text(encoding="utf-8")
                crop = ROOT / reading["detail_crop_path"]
                assert crop.is_file() and hashlib.sha256(crop.read_bytes()).hexdigest() == reading["detail_crop_sha256"]
            for reading in collation.get("resolved_readings", []):
                assert reading["printed_page"] in printed_pages
                assert reading["version_id"] in collation["version_ids"]
                assert reading["status"] == "resolved-human-reviewed"
                assert reading["resolved_on"] and reading["resolution_basis"]
                v = next(v for v in versions if v["id"] == reading["version_id"])
                assert reading["id"] in v["review"]["resolved_reading_ids"]
                assert reading["id"] not in v["review"]["unresolved_reading_ids"]
                body = (ROOT / v["lyrics_path"]).read_text(encoding="utf-8")
                lyrics = body.split("```text\n", 1)[1].split("```", 1)[0]
                assert reading["marker"] not in lyrics
                assert reading["resolved_line"] in lyrics.splitlines()
                crop = ROOT / reading["detail_crop_path"]
                assert crop.is_file() and hashlib.sha256(crop.read_bytes()).hexdigest() == reading["detail_crop_sha256"]
        else:
            for difference in collation["wording_differences"]:
                assert difference["preface"] and difference["score"]
                assert difference["preface_printed_page"] in printed_pages
                assert difference["score_printed_page"] in printed_pages
            for difference in collation["web_transcription_differences"]:
                assert difference["printed_page"] in printed_pages
        for version_id in collation["version_ids"]:
            v = next(v for v in versions if v["id"] == version_id)
            assert v["review"]["collation_record"] == str(p.relative_to(ROOT))
            assert v["review"]["collation_report"] == collation["report_path"]
            assert v["review"]["scope"]
    # Score editions and partial publication claims are separate from lyric counts.
    score_ids = set()
    for p in (ROOT / "data/score-editions").glob("*.json"):
        score = json.loads(p.read_text(encoding="utf-8"))
        assert score["id"] == p.stem and score["id"] not in score_ids
        score_ids.add(score["id"])
        assert score["kind"] == "printed-score-edition" and score["source_id"] in source_ids
        assert (ROOT / score["review"]["report_path"]).is_file()
        assert set(score["related_lyric_version_ids"]) <= set(vids)
        assert score["publication_year_basis"] and score["shelfmark"]
        assert not score["counts_as_new_lyric_identity"] and not score["counts_as_new_lyric_full_text"]
        images = score["images"]
        assert len(images) == score["downloaded_view_count"] == score["manifest_view_count"]
        assert [im["view"] for im in images] == list(range(1, len(images) + 1))
        assert score["visually_reviewed_views"] == [im["view"] for im in images]
        assert sum(im["contains_independent_printed_content"] for im in images) == score["catalogued_printed_pages"]
        assert len({im["url"] for im in images}) == len(images)
        for evidence in images + score["metadata_snapshots"]:
            assert urlparse(evidence["url"]).scheme == "https"
            assert evidence["snapshot_bytes"] > 0 and re.fullmatch(r"[0-9a-f]{64}", evidence["snapshot_sha256"])
            assert not evidence["snapshot_distributed_in_repository"]
        for im in images:
            assert im["width"] > 0 and im["height"] > 0 and im["role"] and im["visually_reviewed_on"]
        assert len(score["stanza_mapping"]) == len(set(score["stanza_mapping"]))
        assert set(score["stanza_mapping"]) <= set(range(1, 7))
    for p in (ROOT / "data/publication-checks").glob("*.json"):
        claim = json.loads(p.read_text(encoding="utf-8"))
        assert claim["id"] == p.stem and claim["kind"] == "publication-claim-check"
        assert claim["source_id"] in source_ids and (ROOT / claim["report_path"]).is_file()
        assert not claim["counts_as_new_lyric_identity"] and not claim["counts_as_new_lyric_full_text"]
        pdf = claim["pdf_evidence"]
        assert pdf["bytes"] > 0 and pdf["pages"] > 0 and not pdf["pdf_distributed_in_repository"]
        assert re.fullmatch(r"[0-9a-f]{64}", pdf["sha256"])
        assert re.fullmatch(r"[0-9a-f]{40}", pdf["sha1"])
        assert pdf["classification"] and pdf["excerpt_scope"] and pdf["attribution_basis"]
        assert all(1 <= page <= pdf["pages"] for page in pdf["visually_reviewed_pdf_pages"])
        assert pdf["printed_target_page"] in pdf["visually_reviewed_pdf_pages"]
        if not claim["original_newspaper_facsimile_obtained"]:
            assert claim["claim_under_review"]["status"] == "not-verified-against-original-newspaper"
            assert claim["open_questions"]
        assert claim["relation_to_kots_1902"]["version_id"] in vids
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
