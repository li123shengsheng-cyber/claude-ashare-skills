#!/usr/bin/env python3
"""ashare.py — A-share market data via Eastmoney public endpoints. Stdlib only.

The helper behind the `claude-ashare-skills` skill pack. No API key, no
third-party dependency, Python 3.9+.

Usage:
    python3 ashare.py limit-up [--date YYYYMMDD] [--file pool.json]
        Today's limit-up pool (default: today, Beijing time), sorted by
        first-seal time, with board ladder, bomb rate and sector counts.
        --file replays a saved getTopicZTPool JSON instead of fetching.

    python3 ashare.py lhb [--date YYYY-MM-DD] [--top N] [--file lhb.json]
        Daily billboard (龙虎榜) summary for a trading day, ranked by net
        buy amount. Data is published after close; for today use a past
        trading day. --file replays a saved datacenter-web JSON.

    python3 ashare.py seats <seat name ...>
        Look up the verified nickname for one or more 龙虎榜 seat names.
        Only the mapping in data/seats.json is used; unknown seats print
        their original name with no nickname — never guessed.

    python3 ashare.py breadth [--date YYYYMMDD]
        Market breadth: advancers/decliners, limit-ups, limit-downs,
        bombed boards and the bomb rate.

Data sources (all free, public Eastmoney endpoints):
    涨停池/炸板池/跌停池  push2ex.eastmoney.com getTopicZTPool/ZBPool/DTPool
    涨跌分布              push2ex.eastmoney.com getTopicZDFenBu
    龙虎榜汇总            datacenter-web.eastmoney.com RPT_DAILYBILLBOARD_DETAILSNEW
    龙虎榜买卖明细        datacenter-web.eastmoney.com RPT_BILLBOARD_DAILYDETAILSBUY/SELL

Nothing here is investment advice. Figures are raw market data; any
judgement (outlook, buy/sell) is the user's own.
"""
import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

EM_UT_EX = "7eea3edcaed734bea9cbfc24409ed989"  # public Eastmoney web token
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0 Safari/537.36"}
HERE = os.path.dirname(os.path.abspath(__file__))


def bj_today(fmt="%Y%m%d"):
    bj = timezone(timedelta(hours=8))
    return datetime.now(bj).strftime(fmt)


def fetch_json(url):
    last = None
    for _ in range(2):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001 - retry once, then report
            last = e
    raise RuntimeError(f"fetch failed: {url}\n  {last}")


def load_file(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def fmt_yi(v):
    if v is None:
        return "--"
    try:
        return f"{float(v) / 1e8:.2f}亿"
    except (TypeError, ValueError):
        return "--"


def fmt_fbt(t):
    if t is None:
        return "--"
    s = str(int(t)).zfill(6)
    return f"{s[:2]}:{s[2:4]}:{s[4:6]}"


# ---------------- limit-up pool ----------------

def zt_pool_url(date, pagesize=200):
    return ("https://push2ex.eastmoney.com/getTopicZTPool?ut=" + EM_UT_EX +
            f"&dpt=wz.ztzt&Pageindex=0&pagesize={pagesize}"
            f"&sort=fbt:asc&date={date}")


def zb_pool_url(date):
    return ("https://push2ex.eastmoney.com/getTopicZBPool?ut=" + EM_UT_EX +
            f"&dpt=wz.ztzt&Pageindex=0&pagesize=1&sort=fbt:asc&date={date}")


def cmd_limit_up(args):
    date = args.date or bj_today()
    if args.file:
        j = load_file(args.file)
    else:
        j = fetch_json(zt_pool_url(date))
    data = j.get("data") or {}
    pool = sorted(data.get("pool") or [], key=lambda d: d.get("fbt") or 999999)
    qdate = str(data.get("qdate") or date)
    print(f"涨停池 {qdate[:4]}-{qdate[4:6]}-{qdate[6:]}  共 {data.get('tc', len(pool))} 家"
          f"（{'盘中快照' if qdate == bj_today() else '收盘数据'}）")
    print(f"{'代码':<8}{'名称':<10}{'现价':>8}{'涨幅':>8}{'首封':>9}{'连板':>5}"
          f"{'封单额':>10}{'换手':>8}  板块")
    for d in pool:
        price = (d.get("p") or 0) / 1000
        print(f"{d.get('c', ''):<8}{d.get('n', ''):<10}{price:>8.2f}"
              f"{(d.get('zdp') or 0):>7.2f}%{fmt_fbt(d.get('fbt')):>9}"
              f"{str(d.get('lbc') or '--'):>5}{fmt_yi(d.get('fund')):>10}"
              f"{(d.get('hs') or 0):>7.2f}%  {d.get('hybk') or '--'}")
    # board ladder
    ladder = {}
    for d in pool:
        ladder[d.get("lbc") or 1] = ladder.get(d.get("lbc") or 1, 0) + 1
    lad = " ".join(f"{k}板×{v}" for k, v in sorted(ladder.items(), reverse=True))
    print(f"\n连板梯队：{lad or '--'}")
    # sector counts
    cnt = {}
    for d in pool:
        k = d.get("hybk") or "其他"
        cnt[k] = cnt.get(k, 0) + 1
    top = sorted(cnt.items(), key=lambda kv: -kv[1])[:5]
    print("涨停最多板块：" + "、".join(f"{k} {v}家" for k, v in top))
    # bomb rate (needs a second call; skip when replaying a file)
    if not args.file:
        try:
            zb = fetch_json(zb_pool_url(date))
            zb_n = (zb.get("data") or {}).get("tc") or 0
            zt_n = data.get("tc") or len(pool)
            if zt_n + zb_n:
                print(f"炸板：{zb_n} 家，炸板率 {zb_n / (zt_n + zb_n) * 100:.1f}%")
        except Exception as e:  # noqa: BLE001 - bomb rate is a bonus stat
            print(f"（炸板数据暂不可用：{e}）")
    return 0


# ---------------- daily billboard (龙虎榜) ----------------

LHB_COLS = ("SECURITY_CODE,SECURITY_NAME_ABBR,TRADE_DATE,CLOSE_PRICE,"
            "CHANGE_RATE,BILLBOARD_NET_AMT,BILLBOARD_BUY_AMT,"
            "BILLBOARD_SELL_AMT,EXPLANATION")


def lhb_url(date, page_size=100):
    return ("https://datacenter-web.eastmoney.com/api/data/v1/get?"
            "reportName=RPT_DAILYBILLBOARD_DETAILSNEW&columns=" +
            urllib.request.quote(LHB_COLS) +
            "&filter=" + urllib.request.quote(f"(TRADE_DATE='{date}')") +
            f"&pageNumber=1&pageSize={page_size}"
            "&sortColumns=BILLBOARD_NET_AMT&sortTypes=-1&source=WEB&client=WEB")


def cmd_lhb(args):
    date = args.date or bj_today("%Y-%m-%d")
    if args.file:
        j = load_file(args.file)
    else:
        j = fetch_json(lhb_url(date))
    rows = (j.get("result") or {}).get("data") or []
    if not rows:
        print(f"{date} 暂无龙虎榜数据（龙虎榜盘后公布；当天请用上一个交易日）。")
        return 0
    # de-duplicate: one stock can appear under several 上榜原因
    seen, out = set(), []
    for r in rows:
        code = r.get("SECURITY_CODE")
        if code in seen:
            continue
        seen.add(code)
        out.append(r)
    out = out[: args.top]
    print(f"龙虎榜 {date}  共 {len(seen)} 只上榜（按净买额排序，前 {len(out)} 只）")
    print(f"{'代码':<8}{'名称':<10}{'收盘':>8}{'涨幅':>8}{'净买额':>12}"
          f"{'买入':>12}{'卖出':>12}  上榜原因")
    for r in out:
        print(f"{r.get('SECURITY_CODE', ''):<8}{r.get('SECURITY_NAME_ABBR', ''):<10}"
              f"{(r.get('CLOSE_PRICE') or 0):>8.2f}"
              f"{(r.get('CHANGE_RATE') or 0):>7.2f}%"
              f"{fmt_yi(r.get('BILLBOARD_NET_AMT')):>12}"
              f"{fmt_yi(r.get('BILLBOARD_BUY_AMT')):>12}"
              f"{fmt_yi(r.get('BILLBOARD_SELL_AMT')):>12}"
              f"  {r.get('EXPLANATION') or '--'}")
    print("\n席位明细与游资绰号：见 skills/lhb-seats —— 席位名以买卖明细接口为准，"
          "绰号只按 data/seats.json 对照表标注，未列入的不猜。")
    return 0


# ---------------- seat nicknames ----------------

def normalize(s):
    for tok in ("股份有限公司", "有限责任公司", "有限公司", "证券", "营业部"):
        s = s.replace(tok, "")
    return s.replace(" ", "").replace("　", "")


def load_seats():
    path = os.path.join(HERE, "data", "seats.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def lookup_seat(seat, data):
    norm = normalize(seat)
    for d in data.get("do_not_label") or []:
        if normalize(d["seat"]) in norm or norm in normalize(d["seat"]):
            return None, d["reason"]
    best = None
    for row in data.get("seats") or []:
        m = normalize(row["match"])
        if m and m in norm:
            if best is None or len(m) > len(normalize(best["match"])):
                best = row
    if best:
        return best["nickname"], best.get("note", "")
    return None, ""


def cmd_seats(args):
    data = load_seats()
    for seat in args.seat:
        nick, note = lookup_seat(seat, data)
        if nick:
            print(f"{seat}  →  {nick}" + (f"（{note}）" if note else ""))
        elif note:
            print(f"{seat}  →  （不标注）{note}")
        else:
            print(f"{seat}  →  （未列入对照表，只显示原名）")
    print("\n席位归属为市场共识，非官方认定；对照表以淘股吧、开盘啦信息为准。")
    return 0


# ---------------- breadth ----------------

def cmd_breadth(args):
    date = args.date or bj_today()
    fenbu = fetch_json("https://push2ex.eastmoney.com/getTopicZDFenBu?ut=" +
                       EM_UT_EX + "&dpt=wz.ztzt")
    zt = fetch_json(zt_pool_url(date, pagesize=1))
    dt = fetch_json("https://push2ex.eastmoney.com/getTopicDTPool?ut=" + EM_UT_EX +
                    f"&dpt=wz.ztzt&Pageindex=0&pagesize=1&sort=fbt:asc&date={date}")
    zb = fetch_json(zb_pool_url(date))
    up = down = flat = 0
    for o in (fenbu.get("data") or {}).get("fenbu") or []:
        k, v = next(iter(o.items()))
        if float(k) > 0:
            up += v
        elif float(k) < 0:
            down += v
        else:
            flat += v
    zt_n = (zt.get("data") or {}).get("tc") or 0
    dt_n = (dt.get("data") or {}).get("tc") or 0
    zb_n = (zb.get("data") or {}).get("tc") or 0
    print(f"市场广度 {date[:4]}-{date[4:6]}-{date[6:]}")
    print(f"上涨 {up} 家 / 下跌 {down} 家 / 平盘 {flat} 家")
    print(f"涨停 {zt_n} 家 / 跌停 {dt_n} 家 / 炸板 {zb_n} 家" +
          (f" / 炸板率 {zb_n / (zt_n + zb_n) * 100:.1f}%" if zt_n + zb_n else ""))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="ashare.py",
                                description="A-share data via Eastmoney public endpoints.")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_zt = sub.add_parser("limit-up", help="today's limit-up pool")
    p_zt.add_argument("--date", help="YYYYMMDD, default today (Beijing)")
    p_zt.add_argument("--file", help="replay a saved getTopicZTPool JSON")
    p_zt.set_defaults(func=cmd_limit_up)

    p_lhb = sub.add_parser("lhb", help="daily billboard summary")
    p_lhb.add_argument("--date", help="YYYY-MM-DD, default today (Beijing)")
    p_lhb.add_argument("--top", type=int, default=20)
    p_lhb.add_argument("--file", help="replay a saved datacenter-web JSON")
    p_lhb.set_defaults(func=cmd_lhb)

    p_se = sub.add_parser("seats", help="look up verified seat nicknames")
    p_se.add_argument("seat", nargs="+", help="seat name(s) as in 龙虎榜")
    p_se.set_defaults(func=cmd_seats)

    p_br = sub.add_parser("breadth", help="market breadth snapshot")
    p_br.add_argument("--date", help="YYYYMMDD, default today (Beijing)")
    p_br.set_defaults(func=cmd_breadth)

    args = p.parse_args(argv)
    try:
        return args.func(args)
    except RuntimeError as e:
        print(f"数据拉取失败：{e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
