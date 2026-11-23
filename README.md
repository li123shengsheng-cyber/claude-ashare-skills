# claude-ashare-skills

Claude Code skills for A-share （中国 A 股） traders — because the trading
skill packs on the trending page are all built for US stocks (Alpaca, FMP,
FINVIZ). A-share traders need different data: 涨停池， 龙虎榜， 游资席位，
连板梯队. This pack speaks that language, using only free public
Eastmoney endpoints. No API key, no paid data, no account.

> A 股交易用的 Claude Code skill 包：涨停复盘 + 龙虎榜游资席位解读。
> 数据全部来自东方财富公开接口，免费、无需 key。
> 美股那套 skill 很好，但 A 股的玩法（涨停、连板、龙虎榜、游资）不在里面——这个包就是补这一块的。

## Skills

| Skill | What it does |
|---|---|
| `limit-up-review` （涨停复盘） | Pull today's limit-up pool, sort by first-seal time, summarise the board ladder, bomb rate and leading sectors. |
| `lhb-seats` （龙虎榜席位解读） | Fetch the daily billboard and label well-known 游资 seats with their verified nicknames. Unknown seats stay unlabeled — never guessed. |

## Quick start

```bash
git clone https://github.com/li123shengsheng-cyber/claude-ashare-skills.git
cd claude-ashare-skills

# Install the skills into Claude Code
cp -r skills/limit-up-review ~/.claude/skills/
cp -r skills/lhb-seats ~/.claude/skills/

# Or just use the helper directly (Python 3.9+, no dependencies)
python3 ashare.py limit-up                  # today's limit-up pool
python3 ashare.py lhb --date 2026-11-20    # 龙虎榜 for a trading day
python3 ashare.py seats "国泰君安证券股份有限公司上海江苏路证券营业部"
python3 ashare.py breadth                   # market breadth snapshot
```

## Example

`python3 ashare.py limit-up` on the morning of 2026-11-23 (intraday
snapshot, 16 limit-ups by 09:40; full output in
[`examples/limit-up-2026-11-23-morning.md`](examples/limit-up-2026-11-23-morning.md)):

```
涨停池 2026-11-23  共 16 家（盘中快照）
代码      名称        现价    涨幅     首封 连板     封单额   换手  板块
002771   真视通     17.40  9.99% 09:25:00    5    2.61亿  7.72%  IT服务Ⅱ
002642   荣联科技    7.99 10.06% 09:30:00    2    4.68亿  4.75%  IT服务Ⅱ
002579   中京电子   14.73 10.01% 09:30:51    3    2.99亿 14.72%  元件
...
连板梯队：5板×1 3板×1 2板×4 1板×10
涨停最多板块：通用设备 3家、光学光电 2家、IT服务Ⅱ 2家、汽车零部 2家、计算机设 2家
```

## Data

- 涨停池 / 炸板池 / 跌停池 / 涨跌分布： `push2ex.eastmoney.com`
  (`getTopicZTPool` / `ZBPool` / `DTPool` / `ZDFenBu`)
- 龙虎榜汇总与买卖明细： `datacenter-web.eastmoney.com`
  (`RPT_DAILYBILLBOARD_DETAILSNEW`,
  `RPT_BILLBOARD_DAILYDETAILSBUY` / `SELL`)
- 游资席位对照表： [`data/seats.json`](data/seats.json) — verified
  2026-11-21 against multiple seat summaries; attribution follows
  淘股吧 and 开盘啦. A seat is listed only when at least two
  independent sources agree. Seats not in the table are never labeled.

## Rules baked into the skills

- Only verified numbers. No invented news, no invented reasons — if no
  verified positive news is found, say 未见明确利好.
- An intraday snapshot is never presented as the close.
- No buy prices, no target prices, no promised returns. These skills
  describe what already happened; decisions are the user's own.

## Disclaimer

本项目仅供学习研究，不构成投资建议。数据来自东方财富公开接口，
席位归属为市场共识，非官方认定。投资有风险，入市需谨慎。

## License

MIT
