#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
12123 车牌选号与号段管理辅助工具
全面支持：
1. 北京市小型新能源汽车（绿牌 · 6位序号 · 京AP/京AG系列）
2. 北京市小型汽车（普通蓝牌 · 5位序号）
3. 双策略引擎：
   - 🎯 低竞争·高命中避坑捡漏模式 (smart): 避开黄牛秒光雷区，优选对子、回文、小顺，成熟号段一次命中率高
   - 👑 极品靓号冲刺模式 (rush): 追求纯豹子、全8全6、顶级顺子，适合刚满7天第一时间抢编
"""

import sys
import os
import json
import datetime
import argparse
from typing import List, Dict, Any, Tuple

# 终端 ANSI 颜色常量
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

DIR_PATH = os.path.dirname(os.path.abspath(__file__))
FUEL_DATA_FILE = os.path.join(DIR_PATH, "segments.json")
NEV_DATA_FILE = os.path.join(DIR_PATH, "segments_nev.json")

class PlateHelper:
    def __init__(self, vehicle_type: str = "nev"):
        self.vehicle_type = vehicle_type.lower()
        self.data_file = NEV_DATA_FILE if self.vehicle_type == "nev" else FUEL_DATA_FILE
        self.segments = []
        self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    self.segments = json.load(f)
                return
            except Exception as e:
                print(f"{YELLOW}读取存档失败: {e}{RESET}")
        self.segments = []

    def get_segment_status(self, seg: Dict[str, Any], now: datetime.datetime = None) -> Dict[str, Any]:
        """计算号段 7 天解锁状态"""
        if now is None:
            now = datetime.datetime.now()
            
        time_str = seg.get("release_time") or seg.get("release_date", "2026-01-01 00:00")
        fmt = "%Y-%m-%d %H:%M" if " " in time_str else "%Y-%m-%d"
        release_dt = datetime.datetime.strptime(time_str, fmt)
        unlock_dt = release_dt + datetime.timedelta(days=7)

        if seg.get("is_first_release"):
            return {
                "unlocked": True,
                "status_text": "🟢 首次投放 (立即解锁自编与随机)",
                "unlock_dt": release_dt,
                "days_unlocked": (now - release_dt).total_seconds() / 86400
            }

        diff = unlock_dt - now
        total_seconds = diff.total_seconds()

        if total_seconds <= 0:
            past_seconds = abs(total_seconds)
            days_past = int(past_seconds // 86400)
            hours_past = int((past_seconds % 86400) // 3600)
            return {
                "unlocked": True,
                "status_text": f"🟢 已解锁自编 (主战场！已开放 {days_past}天{hours_past}小时)",
                "unlock_dt": unlock_dt,
                "days_unlocked": past_seconds / 86400
            }
        else:
            days = int(total_seconds // 86400)
            hours = int((total_seconds % 86400) // 3600)
            mins = int((total_seconds % 3600) // 60)
            urgency = "⚡️即将解锁" if total_seconds <= 86400 else "🟡仅限随机保护期"
            return {
                "unlocked": False,
                "status_text": f"{urgency} (还需 {days}天{hours}小时{mins}分 解锁自编，建议用随机刷)",
                "unlock_dt": unlock_dt,
                "days_unlocked": -total_seconds / 86400
            }

    def check_eligibility(self):
        """展示所有号段的当前解锁状态"""
        now = datetime.datetime.now()
        type_name = "⚡️ 北京市小型新能源汽车（绿牌 · 6位编码 · 京AP/京AG系列）" if self.vehicle_type == "nev" else "🚗 小型普通汽车（蓝牌 · 5位编码）"
        theme_color = GREEN if self.vehicle_type == "nev" else CYAN

        print(f"\n{BOLD}{theme_color}══════════════════════════════════════════════════════════════════{RESET}")
        print(f"{BOLD}{theme_color}  12123 号段公布看板与 7 天自编解锁追踪器  ({now.strftime('%Y-%m-%d %H:%M:%S')}){RESET}")
        print(f"  当前号牌种类: {BOLD}{type_name}{RESET}")
        print(f"{BOLD}{theme_color}══════════════════════════════════════════════════════════════════{RESET}")
        print(f"{DIM}交管12123规则：新号段投放7日内仅供随机选号；满7日后系统随机投放到自编选号池。{RESET}\n")

        sorted_segs = sorted(self.segments, key=lambda s: s.get("release_time", ""), reverse=True)

        for idx, seg in enumerate(sorted_segs, 1):
            info = self.get_segment_status(seg, now)
            width = 4 if self.vehicle_type == "nev" else 3
            start_fmt = f"{seg['start']:0{width}d}" if isinstance(seg['start'], int) else str(seg['start'])
            end_fmt = f"{seg['end']:0{width}d}" if isinstance(seg['end'], int) else str(seg['end'])
            
            if self.vehicle_type == "nev" and seg['prefix'].startswith("京A") and len(seg['prefix']) >= 3:
                display_prefix = f"京A·{seg['prefix'][2:]}"
            else:
                display_prefix = seg['prefix']
                
            range_str = f"{display_prefix}{start_fmt} ~ {display_prefix}{end_fmt}"
            unlock_time_str = info["unlock_dt"].strftime("%Y-%m-%d %H:%M")

            print(f"[{idx:02d}] {BOLD}{range_str:<26}{RESET} 投放: {seg['release_time']} | 解锁: {unlock_time_str}")
            print(f"     状态: {info['status_text']}")
            if seg.get("desc"):
                print(f"     备注: {DIM}{seg['desc']}{RESET}")
        print(f"{theme_color}──────────────────────────────────────────────────────────────────{RESET}\n")

    def generate_smart_candidates(
        self,
        prefix: str,
        start_num: int,
        end_num: int,
        exclude_digits: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        🎯 低竞争 · 高命中避坑捡漏策略生成器：
        专门挑选：绝对不含 4，避开被黄牛脚本秒杀的全豹子/全8全6，
        主攻中端巧思号（对子、回文对称、小顺子、含 1~2 个 8 或 6），成熟号段一次命中率高！
        """
        exclude_digits = [str(d) for d in (exclude_digits or ['4'])]
        width = 4 if self.vehicle_type == "nev" else 3
        pool = []

        for i in range(start_num, end_num + 1):
            s = f"{i:0{width}d}"

            # 1. 绝对硬性排除（如 4）
            if any(bad in s for bad in exclude_digits):
                continue

            # 2. 避开绝对大热死斗号（秒杀号，成熟号段基本100%已被占用，盲试只会白白烧掉20次机会）
            if s in ("8888", "6666", "9999", "888", "666", "999", "1688", "88888", "66666"):
                continue
            if s.count("8") >= 3 or s.count("6") >= 3:
                continue

            score = 0
            tags = []

            if len(s) == 4:
                # 尾双叠 (如 0388, 0366, 0399)
                if s[2] == s[3] and s[1] != s[2]:
                    score += 5
                    tags.append(f"尾双叠({s[2:]})")
                # ABAB对子 (如 0303, 8686)
                if s[0] == s[2] and s[1] == s[3] and s[0] != s[1]:
                    score += 7
                    tags.append(f"ABAB对称({s})")
                # ABBA对称 (如 0330, 8668)
                elif s[0] == s[3] and s[1] == s[2] and s[0] != s[1]:
                    score += 6
                    tags.append(f"ABBA回文({s})")
                # 小顺子
                digits = [int(c) for c in s]
                if digits[1] + 1 == digits[2] and digits[2] + 1 == digits[3]:
                    score += 6
                    tags.append(f"尾三顺({s[1:]})")
                elif digits[0] + 1 == digits[1] and digits[1] + 1 == digits[2]:
                    score += 5
                    tags.append(f"前三顺({s[:3]})")

            elif len(s) == 3:
                digits = [int(c) for c in s]
                if digits[0] == digits[1] or digits[1] == digits[2] or digits[0] == digits[2]:
                    score += 4
                    tags.append(f"对子/夹心({s})")
                if digits[0] + 1 == digits[1] and digits[1] + 1 == digits[2]:
                    score += 6
                    tags.append(f"小顺子({s})")

            # 适量包含 6 或 8 (1~2个，竞争适中吉利好记)
            count_8 = s.count("8")
            count_6 = s.count("6")
            if count_8 in (1, 2):
                score += count_8 * 3
                tags.append(f"带{count_8}个8")
            if count_6 in (1, 2):
                score += count_6 * 2
                tags.append(f"带{count_6}个6")

            # 尾数吉利奖励
            if s[-1] in ("8", "6", "9"):
                score += 2

            if score > 0:
                if self.vehicle_type == "nev" and prefix.startswith("京A") and len(prefix) >= 3:
                    plate_display = f"京A·{prefix[2:]}{s}"
                else:
                    plate_display = f"{prefix}{s}"

                pool.append({
                    "plate": plate_display,
                    "prefix": prefix,
                    "number": s,
                    "score": score,
                    "tags": tags,
                    "strategy": "低竞争·高命中优选"
                })

        pool.sort(key=lambda x: (-x["score"], x["number"]))
        return pool

    def generate_rush_candidates(
        self,
        prefix: str,
        start_num: int,
        end_num: int,
        exclude_digits: List[str] = None,
        prioritize_digits: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        👑 极品靓号冲刺模式生成器：
        追求顶级大豹子、全8全6、经典大顺子，适合刚满7天第一时间抢编！
        """
        exclude_digits = [str(d) for d in (exclude_digits or ['4'])]
        prioritize_digits = [str(d) for d in (prioritize_digits or ['8', '6', '9'])]
        width = 4 if self.vehicle_type == "nev" else 3
        pool = []

        for i in range(start_num, end_num + 1):
            s = f"{i:0{width}d}"
            if any(bad in s for bad in exclude_digits):
                continue

            digits = [int(c) for c in s]
            score = 0
            tags = []

            # 豹子
            if len(set(digits)) == 1:
                score += 200
                tags.append(f"👑 顶级绝品豹子({s})")
            elif len(s) >= 4 and any(s.count(str(d)*3) > 0 for d in range(10)):
                score += 100
                tags.append(f"👑 三连经典豹子({s})")

            # 顺子
            if all(digits[j] + 1 == digits[j+1] for j in range(len(digits)-1)):
                score += 150
                tags.append(f"📈 经典大顺子({s})")

            # 对子/双对
            if len(s) == 4 and s[0] == s[1] and s[2] == s[3] and s[0] != s[2]:
                score += 90
                tags.append(f"👯 AABB双对({s})")

            fav_count = sum(s.count(g) for g in prioritize_digits)
            score += fav_count * 20
            if '8' in s: score += s.count('8') * 6
            if '6' in s: score += s.count('6') * 4

            if self.vehicle_type == "nev" and prefix.startswith("京A") and len(prefix) >= 3:
                plate_display = f"京A·{prefix[2:]}{s}"
            else:
                plate_display = f"{prefix}{s}"

            pool.append({
                "plate": plate_display,
                "prefix": prefix,
                "number": s,
                "score": score,
                "tags": tags or ["常规偏好"],
                "strategy": "极品靓号冲刺"
            })

        pool.sort(key=lambda x: (-x["score"], x["number"]))
        return pool

def main():
    parser = argparse.ArgumentParser(description="12123车牌选号辅助工具（双策略支持：低竞争捡漏 vs 极品冲刺）")
    parser.add_argument("--type", choices=["nev", "fuel"], default="nev", help="号牌种类: nev(小型新能源绿牌, 默认) 或 fuel(普通蓝牌)")
    parser.add_argument("--strategy", choices=["smart", "rush"], default="smart", help="选号策略: smart(低竞争·高命中避坑捡漏, 默认) 或 rush(极品靓号冲刺)")
    parser.add_argument("--check", action="store_true", help="查看号段7天自编解锁状态")
    parser.add_argument("--prefix", type=str, default=None, help="目标号段前缀 (如 绿牌: 京APT 或 京APY; 蓝牌: 京AJE)")
    parser.add_argument("--start", type=int, default=None, help="起始数字 (如 300)")
    parser.add_argument("--end", type=int, default=None, help="结束数字 (如 399)")
    parser.add_argument("--exclude", type=str, default="4", help="排除的数字 (默认: 4)")
    parser.add_argument("--limit", type=int, default=20, help="输出备选车牌数量上限 (默认: 20)")
    args = parser.parse_args()

    helper = PlateHelper(vehicle_type=args.type)

    if args.check or (args.prefix is None and args.start is None):
        helper.check_eligibility()
        print(f"{BOLD}💡 提示：使用 --strategy smart 可查看低竞争高命中避坑组合，--strategy rush 可冲刺顶级豹子！{RESET}\n")

    if args.prefix and args.start is not None and args.end is not None:
        exclude_list = [d.strip() for d in args.exclude.split(",") if d.strip()]
        
        if args.strategy == "smart":
            candidates = helper.generate_smart_candidates(
                prefix=args.prefix,
                start_num=args.start,
                end_num=args.end,
                exclude_digits=exclude_list
            )
            title = "🎯 低竞争 · 高命中避坑捡漏自编优选（避开黄牛秒光雷区，稳妥一次命中）"
        else:
            candidates = helper.generate_rush_candidates(
                prefix=args.prefix,
                start_num=args.start,
                end_num=args.end,
                exclude_digits=exclude_list
            )
            title = "👑 极品靓号冲刺方案（适合刚满7天第一时间抢编）"

        theme_color = GREEN if args.type == "nev" else CYAN
        type_str = "小型新能源绿牌 (6位编码)" if args.type == "nev" else "普通蓝牌 (5位编码)"

        print(f"\n{BOLD}{theme_color}==================================================================={RESET}")
        print(f"{BOLD}{theme_color}  {title}{RESET}")
        print(f"  目标号段: [{args.prefix}{args.start} ~ {args.prefix}{args.end}] ({type_str}) | 排除: [{','.join(exclude_list)}]")
        print(f"{BOLD}{theme_color}==================================================================={RESET}")
        print(f"{'名次':<6} {'车牌号':<16} {'综合推荐分':<12} {'巧思特征标签'}")
        print("-" * 65)
        for rank, item in enumerate(candidates[:args.limit], 1):
            tag_display = " ".join(item["tags"]) if item["tags"] else "顺眼优选"
            print(f"#{rank:02d}    {BOLD}{item['plate']:<16}{RESET} {item['score']:<12} {tag_display}")
        print("-" * 65)
        print(f"共生成 {len(candidates)} 个高性价比备选号。建议挑选前 5~10 个按优先级录入 12123 自编清单！\n")

if __name__ == "__main__":
    main()
