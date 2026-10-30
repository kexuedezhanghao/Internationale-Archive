"""Shared reading labels; underlying research and rights records stay authoritative."""

LANGUAGE_NAMES = {"fr": "French", "en": "English", "de": "German", "ru": "Russian", "zh": "Chinese"}
COLLATION_LABELS = {
    "completed": "所述歌词范围已核对影印",
    "reviewed": "所述歌词范围已核对影印",
    "completed-with-differences-recorded": "已对照影印，网页转录差异另记",
    "reviewed-with-unresolved-readings": "已据版面转录，仍有未决疑读",
    "web-compared-to-specified-historical-editions": "网页已与指定刊本比较，完整校勘或底本身份仍待核",
    "structure-and-selected-variants-reviewed": "仅核结构及部分异文，完整校勘待进行",
    "crop-inspected-full-page-pending": "已核原报局部，整版及完整校勘待进行",
    "facsimile-inspected-transcription-pending": "已取得原刊整版，完整转录待进行",
    "pending": "原刊校勘待进行",
    "not-applicable": "不适用历史原刊校勘",
}
RIGHTS_LABELS = {
    "public-domain-supported": "有公有领域依据",
    "open-license-verified": "开放许可已核",
    "permission-verified": "转载授权已核",
    "author-license-not-specified": "作者尚未指定许可",
    "unassessed": "权利待核",
    "index-only": "仅索引，公开全文权利依据待补",
}
JURISDICTIONS = {"US": "美国", "CN": "中国大陆", "life-plus-70 countries": "作者终身加70年地区"}


def presentation(version):
    review, rights = version["review"], version["rights"]
    collation = review["facsimile_collation"]
    # Unknown statuses must receive a deliberate label rather than silently
    # presenting a new research state as completed.
    label = COLLATION_LABELS[collation]
    if review["status"] == "digital-edition-score-transcribed":
        label = "数字版唱词已转录，原刊及独立刊本对照待补"
    elif review["status"] == "digital-edition-score-reviewed":
        label = "数字版词谱已检查，完整校勘待进行"
    territories = [JURISDICTIONS.get(j, j) for j in rights.get("jurisdictions_considered", [])]
    rights_label = RIGHTS_LABELS[rights["status"]]
    if territories:
        rights_label += "（" + "、".join(territories) + "）"
    reports = []
    for key, title in [("collation_report", "影印对照"), ("source_check_report", "出处与校勘记录")]:
        path = review.get(key)
        if path and path not in [r["path"] for r in reports]:
            reports.append({"label": title, "path": path})
    mapping = "、".join(map(str, version["stanza_mapping"])) or "待核对"
    for detail in version.get("stanza_mapping_details", []):
        extra = "、".join(map(str, detail["additional_french_stanzas"]))
        mapping += f"；刊本第{detail['printed_stanza']}段亦涉及法文第{extra}段"
    return {
        "collation": label,
        "rights": rights_label,
        "mapping": mapping,
        "reports": reports,
        "language_name": LANGUAGE_NAMES.get(version["language"]["tag"], version["language"]["label_zh"]),
    }


def build_presentations(versions):
    return {v["id"]: presentation(v) for v in versions}
