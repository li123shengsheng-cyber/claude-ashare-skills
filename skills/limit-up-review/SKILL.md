---
name: limit-up-review
description: A-share limit-up review — fetch today's limit-up pool from Eastmoney, rank by first-seal time, and summarise the board ladder, bomb rate and leading sectors. Use when the user asks for a 涨停复盘, today's limit-ups, 连板梯队, 炸板率, or which stocks are likely to continue tomorrow.
---

# Limit-Up Review （涨停复盘）

## What it does

Pulls the day's limit-up pool from Eastmoney's public endpoint, sorts by
first-seal time （首封时间）, and produces a review table plus the board
ladder （连板梯队）, bomb rate （炸板率） and leading sectors. No API key.
No paid data. Everything comes from the pool response.

## Quick use

```bash
python3 ashare.py limit-up                 # today (Beijing time)
python3 ashare.py limit-up --date 20261120 # a past trading day
python3 ashare.py breadth                  # advancers / limit-ups / bombs
```

Or read the endpoint directly:

```
https://push2ex.eastmoney.com/getTopicZTPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pagesize=200&sort=fbt:asc&date=YYYYMMDD
```

Response: `data.tc` = total count, `data.qdate` = data date,
`data.pool[]` = one row per stock.

## Field map (pool row)

| Field | Meaning | Notes |
|---|---|---|
| `c` | code, e.g. `002642` | |
| `n` | name, e.g. `荣联科技` | |
| `p` | price × 1000 | divide by 1000 → yuan |
| `zdp` | change % | ~10.0 for main board, ~20.0 for ChiNext/STAR |
| `fbt` / `lbt` | first / last seal time, HHMMSS | `92500` = 09:25:00 (auction seal) |
| `lbc` | consecutive boards （连板数） | 1 = 首板 |
| `zttj.days` / `zttj.ct` | N days / N boards | e.g. 5天5板 |
| `fund` | seal amount （封单额， yuan) | compare with `ltsz` |
| `ltsz` | free-float market cap （流通市值， yuan) | 封单额/流通市值 = 封单比 |
| `hs` | turnover % | high turnover + high boards = divergence risk |
| `hybk` | sector （行业板块） | group counts by this |
| `zbc` | times the board broke （炸板次数） | >0 means it broke and re-sealed |
| `amount` | day turnover （成交额， yuan) | |

Bomb rate needs a second call — the bombed-board pool:

```
https://push2ex.eastmoney.com/getTopicZBPool?ut=...&dpt=wz.ztzt&Pageindex=0&pagesize=1&sort=fbt:asc&date=YYYYMMDD
```

Bomb rate = `ZB.tc / (ZT.tc + ZB.tc)`. Limit-down pool is `getTopicDTPool`
(same params; note `dpt` must stay `wz.ztzt` — `wz.dtzt` returns rc 206).

## How to review (screening rules)

1. **Sort by first-seal time.** Early seal + no break (`zbc` = 0) is
   stronger than a late seal. Auction seals (09:25:00) with big `fund`
   are the strongest open.
2. **Read the ladder.** Count stocks by `lbc`: how many 2板 / 3板 / 4板+.
   A broken ladder (e.g. no 3板 while 2板 is crowded) means the
   theme is not advancing.
3. **Check seal strength.** 封单比 = `fund / ltsz`. Above ~5% is solid;
   below ~1% with high turnover is weak — it can open tomorrow.
4. **Watch turnover divergence.** High `hs` (>15%) on a high board
   with a small seal often means chips are changing hands, not locking up.
5. **Group by `hybk`.** The sector with the most limit-ups is the day's
   strongest theme; check whether its leader is a high board or a first board.
6. **Note the bomb rate.** Above ~30% the market is weak — even good
   seals deserve a discount the next day.

## What NOT to do

- Never invent a reason （利好/题材） for a stock. If no verified news
  is found, write "未见明确利好".
- Never present an intraday snapshot as the close. Mark it 盘中快照
  with the time, and re-fetch after 15:00 for the final table.
- Never give a buy price or a target price. This skill describes what
  already happened; the user decides what to do next.
- Do not use the `getTopicZBPool`/`DTPool` numbers as "tomorrow's picks"
  on their own — they are context, not a signal.
