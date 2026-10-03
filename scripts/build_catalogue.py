#!/usr/bin/env python3
"""Build readable indexes and a self-contained offline browser from JSON."""
from __future__ import annotations

import csv
import html
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def md(value):
    return str(value or "—").replace("|", "\\|").replace("\n", " ")


def main():
    entries = load("data/discoveries/antiwarsongs.json")
    versions = load("data/versions.json")
    snapshot = load("data/discoveries/antiwarsongs.snapshot.json")
    catalogue = ROOT / "catalogue"
    catalogue.mkdir(exist_ok=True)
    groups = defaultdict(list)
    for r in entries:
        groups[r["language_label_as_reported"] or "Supporting material / 未标语言"].append(r)
    index = ["# 《国际歌》发现目录", "", "生成来源：`data/discoveries/antiwarsongs.json`。", "",
             f"本次快照：**{len(entries)} 个来源条目**，其中 **{snapshot['entries_with_lyrics']} 项在原站有歌词**。这些数字包含转写、回译、改编和资料，**不是独立译本数量**。", "",
             "原站索引自称170种语言；本次页面的语言筛选标签有138种，两者采用不同口径。尚未完成标准语言代码归一与版本去重。", "",
             "已整理的正文与身份记录：[历史版本](versions.md)。也可以打开 [离线检索页](../catalogue.html)。", ""]
    for language in sorted(groups, key=str.casefold):
        rows = groups[language]
        index.extend([f"## {language}", "", "| 来源条目 | 类型建议 | 原站有歌词 | 核对状态 |", "|---|---|---|---|"])
        for r in rows:
            index.append(f"| [{md(r['title_as_reported'])}]({r['source_url']}) | {md(r['kind_suggestion'])} | {'是' if r['has_lyrics_at_source'] else '否'} | {md(r['review_status'])} |")
        index.append("")
    (catalogue / "README.md").write_text("\n".join(index), encoding="utf-8")
    vi = ["# 已整理的历史版本与关联作品", "", "文本是否已收录、出处是否已核对、权利是否已核对分别记录。`source-reviewed` 不等于已与原刊逐字校勘。", "",
          "| 语言 | 版本 | 年代/底本 | 法文段落对应 | 全文 |", "|---|---|---|---|---|"]
    for v in versions:
        title = md(v["title_zh"])
        if v["lyrics_path"]:
            title = f"[{title}](../{v['lyrics_path']})"
        else:
            title = f"[{title}]({v['sources'][0]['url']})"
        mapping = ', '.join(map(str, v['stanza_mapping'])) if v['stanza_mapping'] else '待核对'
        for detail in v.get('stanza_mapping_details', []):
            extra = '、'.join(map(str, detail['additional_french_stanzas']))
            mapping += f"；刊本第{detail['printed_stanza']}段亦涉及法文第{extra}段"
        vi.append(f"| {md(v['language']['label_zh'])} | {title} | {md(v['edition_label'])} | {md(mapping)} | {'已收录' if v['lyrics_path'] else '仅索引'} |")
    vi += ["", "具体出处、底本、权利依据和待核对事项见 [versions.json](../data/versions.json)。", ""]
    (catalogue / "versions.md").write_text("\n".join(vi), encoding="utf-8")
    with (catalogue / "discoveries.csv").open("w", encoding="utf-8-sig", newline="") as f:
        fields = ["id", "language_label_as_reported", "html_lang_as_reported", "title_as_reported", "kind_suggestion", "has_lyrics_at_source", "year_mentions_in_heading", "source_submission_date", "review_status", "rights_status", "source_url", "canonical_version_ids"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in entries:
            w.writerow({k: "; ".join(map(str,r[k])) if isinstance(r[k], list) else r[k] for k in fields})
    stats = {
        "source_entries": len(entries),
        "entries_with_lyrics_at_source": sum(r["has_lyrics_at_source"] for r in entries),
        "supporting_entries": sum(not r["has_lyrics_at_source"] for r in entries),
        "source_language_labels": snapshot["source_language_labels"],
        "source_claimed_languages": snapshot["source_claimed_languages"],
        "curated_records": len(versions),
        "local_full_texts": sum(bool(v["lyrics_path"]) for v in versions),
        "independent_version_total": None,
        "kind_suggestions": dict(sorted(Counter(r["kind_suggestion"] for r in entries).items())),
    }
    (ROOT / "data/stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    # Escape '<' so untrusted source headings cannot close the data script.
    payload = json.dumps({"entries":entries,"versions":versions,"stats":stats}, ensure_ascii=False).replace("<", "\\u003c")
    template = (ROOT / "scripts/catalogue.template.html").read_text(encoding="utf-8")
    (ROOT / "catalogue.html").write_text(template.replace("__CATALOGUE_JSON__", payload), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
