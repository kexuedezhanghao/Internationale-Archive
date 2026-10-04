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

## 图书来源记录

`data/discoveries/song-yiwei-2022.json` 独立保存2022年史料书前两编的44项文献条目，与网页目录分开计数。它们不自动增加 `data/stats.json` 中的独立版本或历史全文数量。

| 字段 | 含义 |
|---|---|
| `book_entry` / `section` | 书中的编号及分编；ID按来源和编号保持稳定 |
| `agent_or_publication_as_reported` | 目录所写的署名、出版物或活动，不一律解释为译者 |
| `year_label_as_reported` | 目录年代标记；不直接等同创作年或本书实际采用的刊本年 |
| `book_page_start` / `pdf_page_start` | 从1开始的起始页；本次扫描正文偏移为17，前置页除外 |
| `review_status` | `toc-reviewed` 表示目录已目视登记，未宣称全文校勘 |
| `header_review_status` | `visually-reviewed` 表示所引题头/出处已目视检查，`pending` 表示尚待检查 |
| `reported_provenance` | 本书报告的原刊、中间编辑本、馆藏或网页出处；附本书/PDF证据页码，尚未独立核实原件 |
| `related_version_ids` | 与既有版本可能相关，供比较导航；不等同已证明为同一文本 |
| `canonical_version_ids` | 完成身份比较后才能建立的明确关联，本轮均留空 |
| `facsimile_collation` / `local_lyrics_path` | 原刊逐字校勘仍待进行；本轮没有收入书中歌词全文 |

扫描SHA-256、字节数、397页总数、目录检查范围及页码实测点在 `song-yiwei-2022.snapshot.json`。源PDF与OCR输出不分发。文字索引由 `scripts/build_book_catalogue.py` 生成。

## 版本身份

`data/versions.json` 中的一条记录对应已辨识或暂定的某份文本/版次。保存语言、译者、底本、年代、段落对应、正文路径、校勘状态、权利与证据。不同版本日期有冲突时可以使用 `null` 和明确的待办说明，不选一个看起来合理的年份填上去。

`source_publication_year`只记可明确采用的刊本年。机构书目仅给约年而题名页无年时，此字段为null；`source_publication_year_estimate`另记`year`、`qualifier: ca`、`basis`和证据URL，展示文字保留约年。机构估年不等于原书印年、译文创作年或最早发表。需要区分期月时另记`source_publication_month`。

`stanza_mapping`记录主要段落对应，不保证逐段严格一一对应。改写合并其他法文段素材时，`stanza_mapping_details`用`printed_stanza`、`predominant_french_stanza`、`additional_french_stanzas`和`scope`说明交叉关系；如Luckhardt四段本第二段后半还涉及法文第三段主题。

`source-reviewed`：已经人工核对网页的身份与提取边界。`facsimile_collation: pending`：尚未由本项目与原刊影印逐字比较。两者不互相替代。

`facsimile-reviewed` 表示声明的歌词范围已经对照影印；`completed-with-differences-recorded` 表示完成比较但保留原网页转录、另外记录差异。检查范围在 `review.scope`；不自动涵盖乐谱数字化或原排版摹真。`related_version_ids` 保存同一译者的前文/谱词等关联，仍分别保留文本身份。

`reviewed-with-unresolved-readings` 表示正文已按影印转录，但仍有显式标记的疑读；记录中须说明位置、候选与尚未解决的原因。`digital-edition-score-transcribed` 与 `digital_edition_review: lyric-transcription-completed` 表示现有数字版的扫描唱词已转录；它不证明原报未重排整版已取得，也不替代全文转载的权利依据。1962年记录因公开依据待补继续为 `index-only`。

## 影印校勘记录

`data/collations/` 保存检查范围、版本ID、原刊与PDF页码、文件摘要、影印的传递来源及词句差异；`docs/collation/` 提供对应的阅读说明。后世重印影像与直接原件扫描明确区分。记录文件和文本摘要可以复核，影印大文件不随仓库分发。

`facsimile-reviewed-with-unresolved-readings` 表示已对照声明范围的版面，但存在显式疑读；不是逐字定稿。疑读标记、候选字、印刷页码和局部路径记录在 `unresolved_readings`。`record_kind: edition-facsimile-vs-web` 的 `edition_differences` 比较原刊扫描与另一版网页，不据此把网页所属刊本标成已校勘。

经人工复核解决的疑读移入 `resolved_readings`，保留原标记、候选读法及裁图，另记 `resolved_on`、`resolved_line` 与 `resolution_basis`；版本以 `resolved_reading_ids` 关联。全部疑读解决后可将所声明范围的 `facsimile_collation` 改为 `completed`，不改变其它刊本的校勘状态。

`data/source-checks/` 的可选 `image_evidence` 登记原报截图、未确认刊本的图片及现代重排材料，保存实际下载文件的字节数、SHA-256、尺寸、来源与目视检查范围。`counts_as_facsimile` 只计本批已检查的原刊影像，可包括明确说明范围的局部截图；不等于取得整版。`crop-inspected-full-page-pending` 表示检查了截图，全文校勘与完整刊本身份尚未完成。裁图不含报头时，期版日期应标明是来源所报，不能冒充由图内直接核验。

可选`pdf_evidence`记录实际PDF的URL、字节数、SHA-256／SHA-1、总页数、已目视检查页、印刷页对应与检查范围。`counts_as_facsimile`只计声明目标的历史刊物，现代论文、总目录与不同译者的候选歌集不自动增加目标原刊数；PDF大文件不分发。双页扫描与前置页以逐页`page_mapping`定位，不能套用未经核实的固定偏移。`publication_dating`保存约年限定，`translator_attribution`区分原页署名与现代研究归属。

`original-publication-page` 标记完整原刊页；`issues` 保存IIIF卷期清单、画布总数、已下载完整页数与核实日期，`publication_parts` 将原刊章号定位到印刷页。计数范围必须区分局部、整版、整期和版本身份；同一第6章跨两页出现不算两个主歌。`facsimile-inspected-transcription-pending` 表示已取得并检查原刊，但尚未完成逐字转录。`preliminary_differences` 是检查到的局部差异，不能当作全部异文清单。`translator_as_printed` 与 `translator_name_in_research` 分别保留原刊署名和研究称名，未核实的姓氏、实名及生卒不据后者补入。

`digital-edition-score-reviewed` 表示已检查数字报刊中的扫描词谱，不表示整版是未经重排的原纸报扫描。可选`digital_edition_evidence`保存PDF摘要、内嵌谱图摘要、期版定位、数字文字/图像区别和检查范围；原图方向规范化不另计见证。`public_download_url`未建立时为null，不借用只有文字的网页地址。版本以`digital_edition_source_id`关联来源；`facsimile_collation`保留原刊逐字对照的待核状态。

## 快照与更新

`data/score-editions/`保存具体乐谱印本，字段包括刊印年份及定年依据、馆藏号、数字幅次、每幅角色与摘要、段落范围、谱面检查范围和相关歌词身份。`catalogued_printed_pages`与`manifest_view_count`分别计正文印刷页和数字幅次；背面须保留而不得计作另一页独立曲谱。未转录的音符不能标作数字化完成。乐谱印本不自动增加`versions.json`的歌词身份或历史全文数量。

`data/publication-checks/`保存尚不能登记为歌词版本的刊载命题，分别记录声称的段落、实际看到的摘引、原报/重排分类、复制品出版年与文件制作年、目视检查页和未核范围。副歌引用与散文释义不等于三段歌词。传播叙述可另记于`claim_history_evidence`：其中的`digital_edition_evidence`保存数字报刊的摘要、显示日期/期版、核读页、短句读法和文字/图片区别；数字页可核见后出的说法，但不自动证明早年刊载事实或原纸报字形。网页转录与数字PDF的独立性须另核。后世方括号署名不直接当作原报印刷署名；未取得原报时不得把机构馆藏线索写成已验证的刊载事实。

`antiwarsongs.snapshot.json` 记录抓取时间、整页字节数与SHA-256，以及导入时的数量核对。HTML原件留在临时研究目录，不随发布包分发。网页后来新增、修订或删除的条目应形成可追踪的目录更新，保留已有人工判断。

Antiwar Songs 的文字/CSV目录、`catalogue.html` 和 `data/stats.json` 从网页发现数据库与版本数据库生成。图书目录使用独立生成脚本，目前未合入离线网页检索。JSON保留完整字段。
