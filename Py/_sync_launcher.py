# -*- coding: utf-8 -*-
"""用最新 mem_read 输出同步 launcher.json 的 mem 快照（前端轮询关闭时也显示新数据）"""
import json, os, sys

ROOT = r"C:\Users\abps\Desktop\DiabloIIToolbox"
mem_out = os.path.join(ROOT, "Py", "_mem_out.json")
launcher = os.path.join(ROOT, "Setting", "launcher.json")

d = json.load(open(mem_out, encoding="utf-8"))
results = d.get("results", {})
l = json.load(open(launcher, encoding="utf-8-sig"))

changed = []
for s in l["slots"]:
    pid = str(s.get("pid", 0))
    m = results.get(pid)
    if not m or m.get("_error"):
        continue
    mem = s.setdefault("mem", {})
    if "界面标记" in m:
        mem["marker"] = m["界面标记"]
    if "登录的战网账号" in m:
        mem["account"] = m["登录的战网账号"]
    if "游戏类型" in m:
        mem["gameType"] = m["游戏类型"]
    if "人物位置索引" in m:
        mem["charIndex"] = m["人物位置索引"]
    if "人物名称" in m:
        mem["charName"] = m["人物名称"]
    if "背包物品" in m and isinstance(m["背包物品"], list):
        mem["bag"] = m["背包物品"]
    if "仓库状态" in m and isinstance(m["仓库状态"], dict):
        mem["stash"] = m["仓库状态"]
    changed.append(pid)

with open(launcher, "w", encoding="utf-8") as f:
    f.write("\ufeff")
    json.dump(l, f, ensure_ascii=False, separators=(",", ":"))

# 验证
l2 = json.load(open(launcher, encoding="utf-8-sig"))
for s in l2["slots"]:
    for b in s.get("mem", {}).get("bag", []):
        if b.get("code") == 520:
            print("launcher.json 520:", b.get("special"), "| quality=", b.get("quality"))
print("已同步槽位:", changed)
