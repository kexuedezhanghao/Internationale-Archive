# 数据模型

## 发现记录

`data/discoveries/antiwarsongs.json` 是来源观察清单。记录ID由原站作品ID与页面锚点组成，不因本项目后来修改译者、年代或语言判断而改名。

| 字段 | 含义 |
|---|---|
| `source_url` / `source_anchor` | 可以回到原站具体条目的地址 |
| `title_as_reported` / `heading_as_reported` | 原站简短标题与识别信息；长正文不复制 |
| `source_heading_shortened` | 原站标题块被截取为简短识别信息 |
| `language_label_as_reported` | 原站自己的语言筛选标签，不是本项目确定的语种 |
| `language_code_as_reported` | 原站内部代码，尚未归一为ISO/BCP 47 |
| `html_lang_as_reported` | 原网页给歌词元素设置的 `lang` 属性，可能不够准确 |
| `kind_suggestion` | 根据标题自动提出的内容类型，需人工确认 |
| `has_lyrics_at_source` | 原网页中存在独立歌词块；不是本仓库收入全文 |
| `year_mentions_in_heading` | 标题出现的年份，未确认是翻译年、出版年还是生卒年 |
| `source_submission_date` | 原站登记条目的时间，不能当作作品年代 |
| `external_links` / `youtube_urls` | 原条目附带的来源和音视频线索，未逐个确认有效性 |
| `canonical_version_ids` | 已关联到的本项目版本身份ID；可以多对一 |
| `review_status` / `rights_status` | 人工整理状态与权利状态 |
| `local_lyrics_path` | 仅在确实收录与此来源相符的本地正文后填写 |

同一译本的转写、变体和录音可保持多个来源观察，但关联同一身份记录。部分“Supporting material”是真正的资料章节，部分是用户评论，均不能当作译本。

## 版本身份

`data/versions.json` 中的一条记录对应已辨识或暂定的某份文本/版次。保存语言、译者、底本、年代、段落对应、正文路径、校勘状态、权利与证据。不同版本日期有冲突时可以使用 `null` 和明确的待办说明，不选一个看起来合理的年份填上去。

`source-reviewed`：已经人工核对网页的身份与提取边界。`facsimile_collation: pending`：尚未由本项目与原刊影印逐字比较。两者不互相替代。

## 快照与更新

`antiwarsongs.snapshot.json` 记录抓取时间、整页字节数与SHA-256，以及导入时的数量核对。HTML原件留在临时研究目录，不随发布包分发。网页后来新增、修订或删除的条目应形成可追踪的目录更新，保留已有人工判断。

`catalogue/`、`catalogue.html` 和 `data/stats.json` 从数据库生成。CSV是便于阅读的导出；JSON保留完整字段。
