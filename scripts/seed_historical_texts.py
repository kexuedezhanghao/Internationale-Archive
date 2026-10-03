#!/usr/bin/env python3
"""Extract the four reviewed historic texts from explicitly supplied snapshots.

This is an edition-specific transcription recipe, not a bulk lyric scraper.
Usage: python scripts/seed_historical_texts.py /path/to/research
Existing changed text files are never silently overwritten.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

from lxml import html

ROOT = Path(__file__).resolve().parents[1]
DAY = "2026-10-03"
AWS = "https://www.antiwarsongs.org/canzone.php?id=2003&lang=en"


def source(url, role="text", **extra):
    return {"url": url, "role": role, **extra}


def record(id, lang, label, title, year, author, death, edition, stanzas, url, oldid, file, notes):
    return {
        "id": id,
        "title_zh": title,
        "language": {"tag": lang, "label_zh": label},
        "original_author": "Eugène Pottier",
        "translator": None if lang == "fr" else author,
        "text_author": author,
        "text_author_death_year": death,
        "composition_year": 1871 if lang == "fr" else None,
        "edition_label": edition,
        "source_publication_year": year,
        "stanza_mapping": stanzas,
        "kind": "original" if lang == "fr" else "translation",
        "lyrics_path": f"lyrics/{lang}/{id}.md",
        "review": {"status": "source-reviewed", "date": DAY, "facsimile_collation": "pending"},
        "rights": {
            "status": "public-domain-supported",
            "scope": "historic underlying text only; not site commentary or recordings",
            "jurisdictions_considered": ["US", "CN", "life-plus-70 countries"],
            "basis": [f"Source edition published in {year}, before 1931.", f"Text author died in {death}, more than 70 years before 2026."],
            "evidence_urls": [url],
        },
        "sources": [source(url), source(oldid, "pinned-transcription")],
        "snapshot_filename": file + ".html",
        "snapshot_sha256": None,
        "notes": notes,
    }


def read_snapshot(folder, name):
    path = folder / (name + ".html")
    raw = path.read_bytes()
    return html.fromstring(raw), hashlib.sha256(raw).hexdigest()


def clean(text):
    text = text.replace("\u200b", "").replace("\ufeff", "").replace("\u00a0", " ")
    text = "\n".join(line.strip() for line in text.splitlines())
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def poem_wikitext(page):
    pieces = []
    for node in page.xpath('//*[contains(concat(" ", @class, " "), " poem ")]'):
        data = json.loads(node.get("data-mw"))
        pieces.append(data["body"]["extsrc"])
    text = "\n".join(pieces)
    text = re.sub(r"\{\{Zeile\|\d+\}\}", "", text)
    text = text.replace("{{em|2}}", "").replace("{{idt}}", "").replace("{{mpom|", "").replace("}}", "").replace("'''", "")
    if "{{" in text:
        raise ValueError("Unexpected wiki template; inspect source before transcribing")
    return clean(text)


def main():
    folder = Path(sys.argv[1])
    records = [
        record("fr-pottier-1908", "fr", "法语", "鲍狄埃原词：1908年刊本", 1908, "Eugène Pottier", 1887,
               "《Chants révolutionnaires》1908年版，第23–25页；创作于1871年", [1,2,3,4,5,6],
               "https://fr.wikisource.org/wiki/L%E2%80%99Internationale",
               "https://fr.wikisource.org/w/index.php?title=L%E2%80%99Internationale&oldid=14171457", "fr-pottier-1908",
               ["正文保留此底本的副歌位置与标点，不改作现代演唱排版。", "这是1908年版的转录，不能当作1871年手稿或1887年初版的逐字影印。"]),
        record("en-kerr-1900", "en", "英语", "Charles Hope Kerr 英译：1900年版网页转录", 1900, "Charles Hope Kerr", 1944,
               "Wikisource 标注发表于《Socialist Songs》（1900）", [1,2,3,4,6],
               "https://en.wikisource.org/wiki/The_Internationale_(Kerr)",
               "https://en.wikisource.org/w/index.php?title=The_Internationale_(Kerr)&oldid=15992758", "en-kerr-1900",
               ["当前网页只列对应原词1、2、3、4、6的五段；不得据此断言1900年原刊也只有五段，原刊校勘待办。", "网页另附的 Alternate chorus 归属未单独核实，已从正文排除；未改写其余措辞。", "首个副歌的引号写法照网页保留，待原刊校勘。"]),
        record("de-lavant-1902", "de", "德语", "Rudolf Lavant 德译：1902年刊本", 1902, "Rudolf Lavant (Richard Cramer)", 1915,
               "Rasche，Berlin，1902年5月；Lieder-Gemeinschaft der Arbeiter-Sängervereinigungen Deutschlands", [1,2,3,4,6],
               "https://de.wikisource.org/wiki/Die_Internationale",
               "https://de.wikisource.org/w/index.php?title=Die_Internationale&oldid=4167524", "de-lavant-1902",
               ["此底本为 Lavant 译本，不能与 Emil Luckhardt 的德语通行译本合并。", "正文仅去除维基行号与排版模板；保留 thun、giebt 等历史拼写。", "底本转录含五段；未自行补译原第五段。"]),
        record("zh-qu-1923", "zh", "中文", "瞿秋白译配：1923年《新青年》版", 1923, "瞿秋白", 1935,
               "《新青年》季刊第1期，1923年6月15日；网页传统字形转录", [1,2,6],
               "https://zh.wikisource.org/wiki/%E5%9C%8B%E9%9A%9B%E6%AD%8C_(%E7%9E%BF%E7%A7%8B%E7%99%BD)",
               "https://zh.wikisource.org/w/index.php?title=%E5%9C%8B%E9%9A%9B%E6%AD%8C_(%E7%9E%BF%E7%A7%8B%E7%99%BD)&oldid=2439856", "zh-qu-1923",
               ["保持网页原字形与段间标志，未做简繁转换或改用1962年通行歌词。", "只收录歌词区，不把历史前言混入正文。", "维基文库对原文与此译文分别提供公有领域说明。"]),
    ]
    author_urls = {
        "fr-pottier-1908": "https://fr.wikisource.org/wiki/Auteur:Eug%C3%A8ne_Pottier",
        "en-kerr-1900": "https://en.wikisource.org/wiki/Author:Charles_Hope_Kerr",
        "de-lavant-1902": "https://de.wikisource.org/wiki/Rudolf_Lavant",
    }
    for v in records:
        page, sha = read_snapshot(folder, v["id"])
        v["snapshot_sha256"] = sha
        if v["id"] in author_urls:
            u = author_urls[v["id"]]
            v["sources"].append(source(u, "author-dates"))
            v["rights"]["evidence_urls"].append(u)
        if v["language"]["tag"] in {"fr", "de"}:
            text = poem_wikitext(page)
        elif v["language"]["tag"] == "zh":
            lyric_list = page.xpath('//div[contains(@class,"prp-pages-output")]/dl')
            if len(lyric_list) != 1:
                raise ValueError("Chinese lyric-list boundary changed")
            verse_lines = []
            for dd in lyric_list[0].xpath(".//dd"):
                copy = html.fromstring(html.tostring(dd))
                for nested in copy.xpath(".//dl|.//span[contains(@class,'pagenum')]"):
                    nested.drop_tree()
                line = clean(copy.text_content())
                if line:
                    verse_lines.append(line)
            text = clean("\n".join(verse_lines))
        else:
            node = page.xpath('//*[contains(concat(" ", @class, " "), " poem ")]')[0]
            for br in node.xpath(".//br"):
                br.tail = "\n" + (br.tail or "").lstrip("\n")
            text = clean(node.text_content())
            text, count = re.subn(r"\(Alternate chorus\).*?(?=We want no condescending saviors)", "", text, flags=re.S)
            if count != 1:
                raise ValueError("Kerr alternate chorus boundary changed")
            text = clean(text)
        if len(text) < (250 if v["language"]["tag"] == "zh" else 400):
            raise ValueError("Unexpectedly short historical transcription")
        document = f"# {v['title_zh']}\n\n底本：{v['edition_label']}。\n\n来源：[网页转录]({v['sources'][0]['url']}) · [固定版本]({v['sources'][1]['url']})。\n\n## 歌词\n\n```text\n{text}\n```\n\n## 版本说明\n\n" + "\n".join("- " + n for n in v["notes"]) + "\n\n权利记录：历史文字有公有领域依据；不涵盖网页评论、现代编曲或录音。详细依据见 [版本数据库](../../data/versions.json)。\n"
        path = ROOT / v["lyrics_path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_text(encoding="utf-8") != document:
            raise ValueError(f"Refusing to overwrite edited transcription: {path}")
        path.write_text(document, encoding="utf-8")
        v["lyrics_sha256"] = hashlib.sha256(document.encode()).hexdigest()
    # Russian early and later texts must not be collapsed into one dated version.
    ru_index = "https://ru.wikisource.org/wiki/%D0%98%D0%BD%D1%82%D0%B5%D1%80%D0%BD%D0%B0%D1%86%D0%B8%D0%BE%D0%BD%D0%B0%D0%BB_(%D0%9F%D0%BE%D1%82%D1%8C%D0%B5)"
    for id, title, edition, year, mapping, sources, notes in [
        ("ru-kots-1902", "Коц 俄译：1902年三段版", "Antiwar Songs 标注1902；俄语维基文库亦记早期译本发表于1902年", 1902, [1,2,6],
         [source(AWS+"#agg1930"), source(ru_index,"version-history")],
         ["原站转录可见混入拉丁字母与疑似错字；未把这些字形直接作为已校勘正文。", "待查1902年原刊与词句，不从后来的六段本拼接冒充原刊。"]),
        ("ru-kots-complete-publication-disputed", "Коц 俄译：后续六段本（年代待核对）", "完整本年代有分歧：俄语维基文库标1937；Antiwar Songs 相关条目标1931", None, [1,2,3,4,5,6],
         [source("https://ru.wikisource.org/wiki/%D0%98%D0%BD%D1%82%D0%B5%D1%80%D0%BD%D0%B0%D1%86%D0%B8%D0%BE%D0%BD%D0%B0%D0%BB_(%D0%9F%D0%BE%D1%82%D1%8C%D0%B5;_%D0%9A%D0%BE%D1%86)"), source(ru_index,"version-history")],
         ["1931和1937可能是不同修订或不同出版节点，原刊证据不足，暂不定年。", "后补三段的出版与权利情况另行核对，不沿用1902年三段本的权利结论。"]),
    ]:
        records.append({"id":id,"title_zh":title,"language":{"tag":"ru","label_zh":"俄语"},"original_author":"Eugène Pottier","translator":"Аркадий Яковлевич Коц","text_author":"Аркадий Яковлевич Коц","source_publication_year":year,"edition_label":edition,"stanza_mapping":mapping,"kind":"translation","lyrics_path":None,"review":{"status":"identity-provisional","date":DAY,"facsimile_collation":"pending"},"rights":{"status":"unassessed","scope":"this specific translation/edition","evidence_urls":[]},"sources":sources,"notes":notes})
    records.append({
        "id":"zh-personal-345-2026", "title_zh":"个人中文可唱译配：原第3、4、5段", "language":{"tag":"zh","label_zh":"中文"},
        "original_author":"Eugène Pottier", "translator":"kexuedezhanghao（个人试作）", "source_publication_year":2026,
        "edition_label":"Internationale-ZH-345 / v0.1.0 首次公开草案", "stanza_mapping":[3,4,5], "kind":"singable-adaptation", "lyrics_path":None,
        "review":{"status":"source-reviewed","date":DAY,"facsimile_collation":"not-applicable"},
        "rights":{"status":"author-license-not-specified","scope":"modern personal adaptation","evidence_urls":["https://github.com/kexuedezhanghao/Internationale-ZH-345/blob/main/README.md"]},
        "sources":[source("https://github.com/kexuedezhanghao/Internationale-ZH-345"),source("https://github.com/kexuedezhanghao/Internationale-ZH-345/blob/main/README.md","license-and-version")],
        "notes":["原仓库明确说许可暂未确定；本档案先以链接记录。", "个人试作，非历史定本或官方译词；版本持续变化时应固定具体提交。"],
    })
    out = ROOT / "data/versions.json"
    out.write_text(json.dumps(records, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    discoveries = ROOT / "data/discoveries/antiwarsongs.json"
    entries = json.loads(discoveries.read_text(encoding="utf-8"))
    mapping = {
        "lyrics_song": ("fr-pottier-1908", "原站为通行转录；关联1908年刊本作对照，尚未断言字句完全相同。"),
        "agg2012": ("zh-qu-1923", "关联1923年瞿秋白译配；原站字形/转写不能计作独立译本。"),
        "agg1930": ("ru-kots-1902", "1902年版线索；转录错字与字形混用待原刊校勘。"),
    }
    for r in entries:
        if r["source_anchor"] in mapping:
            vid, note = mapping[r["source_anchor"]]
            r["canonical_version_ids"] = [vid]
            r["review_status"] = "linked-needs-collation"
            r["notes"] = [note]
    discoveries.write_text(json.dumps(entries, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    print(f"Curated {len(records)} records; transcribed four historic texts.")


if __name__ == "__main__":
    main()
