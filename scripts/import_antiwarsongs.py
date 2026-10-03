#!/usr/bin/env python3
"""Import factual discovery metadata, never lyrics or article bodies, from AWS.

Usage: python scripts/import_antiwarsongs.py downloaded-page.html
Dependency: lxml. Keep the downloaded HTML outside the repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

from lxml import html

ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "https://www.antiwarsongs.org/canzone.php?id=2003&lang=en"


def cssclass(name: str) -> str:
    return f'contains(concat(" ", normalize-space(@class), " "), " {name} ")'


def lines(node) -> list[str]:
    copy = html.fromstring(html.tostring(node))
    for el in copy.xpath(".//script|.//style|.//img"):
        el.drop_tree()
    for el in copy.xpath(".//br"):
        el.tail = "\n" + (el.tail or "")
    return [re.sub(r"\s+", " ", s).strip() for s in copy.text_content().splitlines() if s.strip()]


def import_page(path: Path) -> tuple[list[dict], dict]:
    raw = path.read_bytes()
    page = html.fromstring(raw)
    records = []
    containers = page.xpath(f'//div[{cssclass("boxsong")} or {cssclass("boxvers")}]')
    toc = {}
    for a in page.xpath('//a[normalize-space(text())=">>>"]'):
        label = re.sub(r"\s+", " ", a.getparent().tail or "").strip()
        toc[a.get("href", "").lstrip("#")] = label
    for box in containers:
        anchors = box.xpath('./a[starts-with(@id,"agg")]/@id')
        is_original = bool(box.xpath('.//*[@id="lyrics_song"]'))
        if not anchors and not is_original:
            continue
        anchor = "lyrics_song" if is_original else anchors[0]
        record_id = "aws-2003-original" if is_original else "aws-2003-" + anchor
        comment = box.xpath(f'./div[{cssclass("commento")}]')
        header = comment[0].xpath("./strong[1]") if comment else []
        raw_heading = lines(header[0]) if header else []
        # Several legacy HTML <strong> elements are unclosed and swallow article
        # paragraphs. Retain short identifying metadata only, never those bodies.
        heading = []
        heading_size = 0
        for line in raw_heading:
            if len(line) > 240 or heading_size + len(line) > 600 or len(heading) >= 8:
                break
            heading.append(line)
            heading_size += len(line)
        if is_original:
            heading = ["L'Internationale", "Eugène Pottier, 1871", "Music: Pierre De Geyter, 1888"]
        title = heading[0] if heading else toc.get(anchor) or f"Supporting material ({anchor})"
        title = title.strip()
        language_link = box.xpath(f'.//div[{cssclass("boxlingua")}]/a[1]')
        label = language_link[0].text_content().strip() if language_link else ("French" if is_original else None)
        code = parse_qs(urlparse(language_link[0].get("href")).query).get("langcode", [None])[0] if language_link else ("fre" if is_original else None)
        lyric_blocks = box.xpath(f'./div[{cssclass("song-lyrics")}]')
        lang_tags = sorted(set(box.xpath(f'./div[{cssclass("song-lyrics")}]//span/@lang')))
        videos = sorted(set(box.xpath(f'.//div[{cssclass("youtubeembed")}]/@id')))
        external_links = []
        for a in box.xpath(".//a[@href]"):
            href = a.get("href")
            parsed = urlparse(href)
            if parsed.scheme not in {"http", "https"} or (parsed.hostname or "").endswith("antiwarsongs.org"):
                continue
            if href not in external_links:
                external_links.append(href)
        date_links = box.xpath('.//a[contains(@href,"filter_maxDate=")]/@href')
        submitted_on = None
        if date_links:
            value = parse_qs(urlparse(date_links[0]).query).get("filter_maxDate", [None])[0]
            if value:
                try:
                    submitted_on = datetime.strptime(value, "%Y-%m-%d").date().isoformat()
                except ValueError:
                    pass
        text = " ".join(heading).lower()
        # Suggestions only: a human must identify independent translations and
        # distinguish transliterations, literal back-translations and recordings.
        if not lyric_blocks:
            kind = "supporting-material"
        elif is_original:
            kind = "original"
        elif any(t in text for t in ["romaniz", "traslitter", "transliter", "grafia", "polytonic", "politon"]):
            kind = "transcription-candidate"
        elif any(t in text for t in ["literal", "letterale", "word-for-word"]):
            kind = "literal-translation-candidate"
        elif any(t in text for t in ["parod", "anticommun", "anti-commun", "anarch", "anticler", "anti-cler", "women", "femmes", "additional verses", "strofe aggiuntive"]):
            kind = "adaptation-candidate"
        else:
            kind = "translation-candidate"
        records.append({
            "id": record_id,
            "source_id": "antiwarsongs-2003",
            "source_anchor": anchor,
            "source_url": SOURCE_URL + "#" + anchor,
            "title_as_reported": title,
            "heading_as_reported": heading,
            "heading_metadata_only": True,
            "source_heading_shortened": len(heading) < len(raw_heading),
            "language_label_as_reported": label,
            "language_code_as_reported": code,
            "language_code_scheme": "AWS internal; not normalized",
            "html_lang_as_reported": lang_tags,
            "kind_suggestion": kind,
            "has_lyrics_at_source": bool(lyric_blocks),
            "lyric_blocks_at_source": len(lyric_blocks),
            "year_mentions_in_heading": sorted(set(int(y) for y in re.findall(r"(?<!\d)(?:1[6-9]\d{2}|20\d{2})(?!\d)", " ".join(heading)))),
            "source_submission_date": submitted_on,
            "external_links": external_links,
            "youtube_urls": ["https://www.youtube.com/watch?v=" + v for v in videos],
            "canonical_version_ids": [],
            "review_status": "unreviewed-discovery",
            "rights_status": "unassessed",
            "local_lyrics_path": None,
            "notes": [],
        })
    ids = [r["id"] for r in records]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate AWS anchors: import aborted")
    all_lyrics = len(page.xpath(f'//div[{cssclass("song-lyrics")}]'))
    indexed_lyrics = sum(r["lyric_blocks_at_source"] for r in records)
    if all_lyrics != indexed_lyrics:
        raise ValueError(f"Unaccounted lyric blocks: {all_lyrics} != {indexed_lyrics}")
    stats = {
        "source_id": "antiwarsongs-2003",
        "source_url": SOURCE_URL,
        "retrieved_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
        "snapshot_sha256": hashlib.sha256(raw).hexdigest(),
        "snapshot_bytes": len(raw),
        "source_entries": len(records),
        "entries_with_lyrics": sum(r["has_lyrics_at_source"] for r in records),
        "lyric_blocks": all_lyrics,
        "source_language_labels": len({r["language_label_as_reported"] for r in records if r["language_label_as_reported"]}),
        "source_claimed_languages": 170,
        "independent_version_count": None,
        "notes": [
            "The 170-language figure is the source's own index claim; it is not a recount.",
            "Entries include supporting material, back-translations, scripts and adaptations.",
            "Submission dates and heading years are not verified publication dates.",
            "No lyrics or article bodies are imported by this script.",
        ],
    }
    return records, stats


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("html_path", type=Path)
    ap.add_argument("--output", type=Path, default=ROOT / "data/discoveries/antiwarsongs.json")
    args = ap.parse_args()
    records, stats = import_page(args.html_path)
    # A refresh never silently replaces human-reviewed annotations.
    if args.output.exists():
        old = json.loads(args.output.read_text(encoding="utf-8"))
        by_id = {r["id"]: r for r in old}
        for r in records:
            if r["id"] in by_id:
                for key in ["canonical_version_ids", "review_status", "rights_status", "local_lyrics_path", "notes"]:
                    r[key] = by_id[r["id"]].get(key, r[key])
        new_ids = {r["id"] for r in records}
        missing = [r["id"] for r in old if r["id"] not in new_ids]
        if missing:
            raise ValueError("Refresh would discard previous discoveries; inspect manually: " + ", ".join(missing))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = args.output.with_name("antiwarsongs.snapshot.json")
    manifest.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
