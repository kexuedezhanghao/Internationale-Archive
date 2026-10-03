# Internationale Archive · 《国际歌》版本档案

收集《国际歌》（L’Internationale）各语言、各时期的译本、可唱译配、异文及相关音源线索，逐版记录出处与权利依据。

项目刚刚开始。**“全版本”是持续收集的目标，不是已经完成的覆盖声明。**

## 现在可以看什么

| 内容 | 数量 | 含义 |
|---|---:|---|
| Antiwar Songs 来源线索 | 509 | 版本、转写、回译、改编、评论、视频和资料条目 |
| 原站附有歌词的条目 | 388 | 这些全文尚未全部收录或核对，不能算作388个独立译本 |
| 其他资料条目 | 121 | 无独立歌词块的评论、介绍和音视频等线索 |
| 已建立身份记录 | 7 | 四份历史文本、两个俄语历史版本线索、一份个人现代译配 |
| 已收录历史全文 | 4 | 法语鲍狄埃、英语 Kerr、德语 Lavant、中文瞿秋白 |

Antiwar Songs 的索引自称170种语言；页面的语言筛选标签有138种。这些标签、方言、古语、人工语言与独立译本的统计口径尚待统一，暂不公布“已覆盖多少语言/多少独立版本”。

- 打开 [离线检索页](catalogue.html)：搜索语言、译者、年代和版本，并筛选来源类型。
- 浏览 [完整文字目录](catalogue/README.md) 或 [已整理版本](catalogue/versions.md)。
- 下载 [来源目录 CSV](catalogue/discoveries.csv)，或读取 [发现数据库](data/discoveries/antiwarsongs.json) 和 [版本数据库](data/versions.json)。
- 查看 [收集进度与待办](docs/ROADMAP.md)、[字段含义](docs/DATA_MODEL.md) 和 [权利记录规则](RIGHTS.md)。

## 首批文本

| 语言 | 译者/作者 | 采用底本 | 说明 |
|---|---|---|---|
| 法语 | Eugène Pottier | [1908年《Chants révolutionnaires》版](lyrics/fr/fr-pottier-1908.md) | 六段原词；不冒充1871年手稿或1887年初版 |
| 英语 | Charles Hope Kerr | [标注1900年的网页转录](lyrics/en/en-kerr-1900.md) | 网页列五段，原刊仍待校勘；归属不明的替代副歌暂不收入 |
| 德语 | Rudolf Lavant | [1902年5月刊本的网页转录](lyrics/de/de-lavant-1902.md) | 五段；不是 Emil Luckhardt 通行译本 |
| 中文 | 瞿秋白 | [1923年《新青年》版的网页转录](lyrics/zh/zh-qu-1923.md) | 对应原第1、2、6段，保留字形，不与现代通行版混同 |

这四份文本已核对网页底本、版次信息与权利依据；**尚未由本项目逐字对照原刊影印完成校勘**。每篇保存固定页面版本与转录说明。

个人中文第3、4、5段译配的母本仍在 [Internationale-ZH-345](https://github.com/kexuedezhanghao/Internationale-ZH-345)。本档案记录其版本、段落对应与来源，保留它自己的许可状态。

## 怎样识别一个版本

按语言、译者、底本、年代、段落取舍与词句变化识别版本。简繁转换、罗马字转写、同一歌词的不同录音通常应关联原版本；独立翻译、补译、改写和历史修订另行登记。

`data/discoveries/` 保存“某网站有这样一个条目”的发现事实。`data/versions.json` 保存经过人工整理的版本身份。发现条目可以关联同一个版本，也可以因为身份、年代或权利未明而继续保持待核对。

## 维护

普通阅读无需安装任何依赖。维护脚本使用 Python 3.10+；导入原站HTML与历史页面时另需 `lxml`。

```bash
python -m pip install -r requirements.txt
python scripts/build_catalogue.py
python scripts/validate.py
```

更新来源目录时，先把原站HTML下载到仓库外，再执行：

```bash
python scripts/import_antiwarsongs.py /path/to/downloaded-page.html
python scripts/build_catalogue.py
python scripts/validate.py
```

导入器保留既有人工标记，遇到来源条目消失会中止，避免静默丢失线索。原站HTML正文与大批未经核权的歌词不随本仓库分发。

欢迎通过 Issue 补充新版本和纠错；提交方式见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 来源与致谢

起点是 [Antiwar Songs / Canzoni Contro la Guerra 的《国际歌》专题](https://www.antiwarsongs.org/canzone.php?id=2003&lang=en)。感谢 Lorenzo Masetti、Riccardo Venturi、Arisztid 及多年贡献者的收集、辨识和研究。本档案是独立整理项目，与原站无隶属关系。

同时参考各语言 Wikisource、[LyricsTranslate 汇编](https://lyricstranslate.com/en/internationale-lyrics.html)、[中文马克思主义文库专题](https://www.marxists.org/chinese/pdf/international.htm) 与原始出版物。当前批量导入范围只有 Antiwar Songs；其他站点没有被宣称已全量导入。

逐条来源见 [sources.json](data/sources.json) 与各版本记录。许可范围见 [LICENSE.md](LICENSE.md)。
