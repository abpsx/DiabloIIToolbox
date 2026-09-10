# -*- coding: utf-8 -*-
import json
d = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Setting\memory\special_names.json", encoding="utf-8"))
names = {en: cn for en, cn in d["set_names"]}
print("json 池 Tancred:", names.get("Tancred's Weird"))
print("updated_at:", d.get("updated_at"))

l = json.load(open(r"C:\Users\abps\Desktop\DiabloIIToolbox\Setting\launcher.json", encoding="utf-8-sig"))
for s in l["slots"]:
    m = s.get("mem", {})
    bag = m.get("bag", [])
    t520 = [b for b in bag if b.get("code") == 520]
    print("slot pid=%s poll=%s" % (s.get("pid"), m.get("poll")))
    for b in t520:
        print("   520 special=%r quality=%s" % (b.get("special"), b.get("quality")))
    print("   stash_open:", m.get("stash", {}).get("stash_open"), "page:", m.get("stash", {}).get("page"))
    print("   updated:", l.get("updated"))
