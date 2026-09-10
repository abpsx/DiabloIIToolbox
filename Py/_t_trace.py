# -*- coding: utf-8 -*-
import random

random.seed(42)

def trace(x0, y0, x1, y1):
    dist = abs(x1 - x0) + abs(y1 - y0)
    steps = max(8, min(24, int(dist / 40) + random.randint(4, 8)))
    mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    arc = max(10, int(dist / 4))
    cx = mx + random.uniform(-arc * 0.3, arc * 0.3)
    cy = my - arc * random.uniform(0.7, 1.2)
    pts = []
    for i in range(1, steps + 1):
        t = i / steps
        t = t * t * (3 - 2 * t)
        u = 1 - t
        x = u * u * x0 + 2 * u * t * cx + t * t * x1
        y = u * u * y0 + 2 * u * t * cy + t * t * y1
        pts.append((int(x), int(y)))
    return pts

# 跨面板: 背包(0,0)中心(871,555) -> 仓库(1,0)中心(581,413)
pts = trace(871, 555, 581, 413)
print("步数", len(pts))
print("前5:", pts[:5])
print("中5:", pts[len(pts)//2-2:len(pts)//2+3])
print("后5:", pts[-5:])
ys = [p[1] for p in pts]
end_min = min(pts[0][1], pts[-1][1])
print("顶点y=%d 端点min=%d 向上弧度=%s" % (min(ys), end_min, "是" if min(ys) < end_min else "否"))
# 间隔检查（顺畅度: 相邻步距是否平滑）
diffs = [abs(pts[i+1][0]-pts[i][0])+abs(pts[i+1][1]-pts[i][1]) for i in range(len(pts)-1)]
print("最大步距=%d 平均步距=%.1f" % (max(diffs), sum(diffs)/len(diffs)))
