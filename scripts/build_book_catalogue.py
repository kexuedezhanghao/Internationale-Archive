#!/usr/bin/env python3
"""Render the book's source index from manually reviewed metadata."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVENANCE_LABELS = {
    'original-publication-reported': '书中所指原刊',
    'intermediate-book-source-reported': '本书采用的编辑本',
    'holding-institution-reported': '书中所记来源机构',
    'comparison-edition-reported': '书中所列对照本',
    'consulted-web-source-reported': '本书采用的网页',
    'consulted-print-edition-reported': '本书采用的刊本',
}


def render(entries):
    reviewed = sum(r['header_review_status'] == 'visually-reviewed' for r in entries)
    lines = [
        '# 《国际歌》在中国：44项文献与底本索引',
        '',
        '宋逸炜编、孙江审校：《〈国际歌〉在中国：〈国际歌〉的译本、底本与传播》，南京大学出版社，2022年5月第1版第1次印刷，ISBN 978-7-305-25673-8。',
        '',
        f'依据本书目录，登记33项中文文献、11项外文底本，已目视检查{reviewed}项正文的题头及出处。**44项是文献条目数，不是44个独立译本，也不是44份已校勘全文。**',
        '',
        '页码采用本书印刷页码，只登记条目起始页。电子文件页序与印刷页码的对应另见[技术核对记录](../docs/BOOK_2022_REVIEW.md)。',
        '',
        '“题头已核”表示已目视检查本书的题头/出处，不代表已取得原刊。“目录已核”表示目录的题名、署名/出版物、年代与起页已登记；正文核对仍待进行。',
        '',
    ]
    for section, title in [(1, '中文文献'), (2, '外文底本')]:
        lines += [f'## {title}', '', '| 编号 | 语言 | 题名 | 署名、出版物或活动（照目录） | 年代标记（照目录） | 本书起页 | 检查范围 |', '|---|---|---|---|---|---:|---|']
        for r in entries:
            if r['section'] != section:
                continue
            status = '题头已核' if r['header_review_status'] == 'visually-reviewed' else '目录已核'
            lines.append(f"| {r['book_entry']} | {r['language_label']} | {r['title_as_reported']} | {r['agent_or_publication_as_reported']} | {r['year_label_as_reported'] or '未标'} | {r['book_page_start']} | {status} |")
        lines += ['']
    lines += ['## 已检查的原刊及中间来源线索', '', '以下书目事实来自本书的出处说明，尚未逐项独立核实原刊。', '']
    for r in entries:
        if not r['reported_provenance']:
            continue
        lines += [f"### {r['book_entry']} · {r['agent_or_publication_as_reported']}", '', f"《国际歌》在中国，第{r['book_page_start']}页。", '']
        for p in r['reported_provenance']:
            lines.append(f"- {PROVENANCE_LABELS[p['kind']]}：{p['citation']}")
        lines += ['']
        for note in r['metadata_notes']:
            lines += [note, '']
    lines += [
        '## 使用与后续核对', '',
        '先按上面的报刊日期、版次和页码寻找原件，再核对歌词字形、段落取舍、副歌和谱词差异。同一译本的不同刊印可以保留多条来源记录，身份去重后再关联。', '',
        '本索引只收书目及来源事实，没有发布本书PDF、扫描页或大批OCR文字。独立取得的1923年《新青年》影印与谱词另见[瞿秋白校勘记录](../docs/collation/zh-qu-1923.md)。第三编“传播”和附录尚未完整索引。', '',
        '数据：[44项来源记录](../data/discoveries/song-yiwei-2022.json) · [扫描及检查范围记录](../data/discoveries/song-yiwei-2022.snapshot.json) · [阅读与核对说明](../docs/BOOK_2022_REVIEW.md)。', '',
        '更新数据后运行 `python scripts/build_book_catalogue.py` 及 `python scripts/validate.py`。', '',
    ]
    return '\n'.join(lines)


def main():
    entries = json.loads((ROOT / 'data/discoveries/song-yiwei-2022.json').read_text(encoding='utf-8'))
    (ROOT / 'catalogue/book-song-2022.md').write_text(render(entries), encoding='utf-8')
    print(f'Built book catalogue: {len(entries)} source entries.')


if __name__ == '__main__':
    main()
