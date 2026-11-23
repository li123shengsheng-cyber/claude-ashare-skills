---
name: lhb-seats
description: A-share 龙虎榜 seat reading — fetch the daily billboard from Eastmoney and label well-known 游资 seats with their verified nicknames. Use when the user asks about 龙虎榜, who bought/sold a stock, 游资动向, or what a seat's nickname is.
---

# LHB Seats （龙虎榜游资席位解读）

## What it does

Fetches the day's 龙虎榜 from Eastmoney's public datacenter endpoint and,
for each stock, lists the buy/sell seats with their verified nicknames
from `data/seats.json`. Seats not in the table are shown by their
original name only — never guessed.

## Quick use

```bash
python3 ashare.py lhb --date 2026-11-20 --top 20   # summary, ranked by net buy
python3 ashare.py seats "国泰君安证券股份有限公司上海江苏路证券营业部"
python3 ashare.py seats "东方证券股份有限公司深圳金田路证券营业部"
```

## Endpoints (all public, no key)

Daily billboard summary — one row per stock per 上榜原因：

```
https://datacenter-web.eastmoney.com/api/data/v1/get?reportName=RPT_DAILYBILLBOARD_DETAILSNEW&columns=SECURITY_CODE,SECURITY_NAME_ABBR,TRADE_DATE,CLOSE_PRICE,CHANGE_RATE,BILLBOARD_NET_AMT,BILLBOARD_BUY_AMT,BILLBOARD_SELL_AMT,EXPLANATION&filter=(TRADE_DATE='YYYY-MM-DD')&pageNumber=1&pageSize=100&sortColumns=BILLBOARD_NET_AMT&sortTypes=-1&source=WEB&client=WEB
```

Key columns: `BILLBOARD_NET_AMT` （净买额）, `BILLBOARD_BUY_AMT`,
`BILLBOARD_SELL_AMT`, `EXPLANATION` （上榜原因， e.g. 日涨幅偏离值达到7%
的前5只证券）. One stock can appear several times under different
reasons — de-duplicate by `SECURITY_CODE` before ranking.

Buy / sell seat details for one stock:

```
reportName=RPT_BILLBOARD_DAILYDETAILSBUY   (and ...SELL)
filter=(SECURITY_CODE="002642")  +  TRADE_DATE if needed
```

Seat rows carry the full seat name, e.g.
`国泰君安证券股份有限公司上海江苏路证券营业部`, the buy/sell amount,
and a seat-type flag: names containing `机构专用` are institutions,
names containing `股通` are northbound (Stock Connect) money.

龙虎榜 is published after close. If the date is today and the market
has not closed, the response is empty — use the previous trading day.

## Seat nickname rules (strict)

The mapping lives in `data/seats.json` (verified 2026-11-21, cross-checked
from multiple seat summaries; attribution follows 淘股吧 and 开盘啦）.

1. **Only table entries.** If a seat is not in the table, show the
   original name with no label. Never infer a nickname from a similar
   road name or from recent activity.
2. **Match broker + road together.** Normalise both sides first
   (strip `股份有限公司` / `证券` / `营业部` and spaces), then
   substring-match. Longest match wins.
3. **Order matters.** Match `华泰证券深圳益田路荣超商务中心`
   （欢乐海岸） before `华泰证券深圳益田路` （徐留胜）.
   `太平南路` must include the broker: 国泰君安/国泰海通 = 作手新一，
   中投/中金财富 = 小鳄鱼 — never match on the road alone.
4. **Shared seats keep both names.** `中信证券上海淮海中路` is
   `赵老哥 / 孙哥`.
5. **Known non-attribution.** `东方证券深圳金田路` is very active but
   has no verified nickname (深南哥's seats are only 光大/申万宏源
   深圳金田路 + 中天证券台州市府大道） — leave it unlabeled.
6. **Broker renames.** 国泰君安 absorbed 海通证券; from 2025-04 the
   surviving name is 国泰海通证券. Old and new names map to the same
   seat and the same nickname.
7. **Institutions are not 游资.** `机构专用` is labeled `机构席位`,
   separately. `东方财富拉萨` seats are labeled
   `拉萨天团（散户集中）` — a crowd, not one trader.

Always add the footnote: 席位归属为市场共识，非官方认定.

## How to read a board

- **Net buy with famous seats on the buy side** (e.g. 章盟主， 赵老哥）
  and institutions selling is a strong-money footprint — but it is
  still only one day's flow, not a promise.
- **One-day wonder:** a seat that appears once and never again is
  noise. Look for the same nickname returning to the same stock or
  theme across days.
- **Sell-side concentration** by two or more famous seats on the same
  day is a warning, especially after several consecutive boards.
- **Ladder context:** combine with the `limit-up-review` skill — a
  龙虎榜 stock that is also a 3板+ leader with an early seal reads
  very differently from a first-board stock with a weak seal.
