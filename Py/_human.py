# -*- coding: utf-8 -*-
"""人性化操作模拟（公共模块）。
- jitter: 点击位置小范围随机偏移（±r px）
- wait:   操作间隔随机扰动
- click:  WM_MOUSEMOVE 贝塞尔轨迹移动到目标（带抖动）-> WM_LBUTTONDOWN/UP
所有脚本统一 import 本模块，保证行为一致。
"""
import random, time, ctypes

_last = None  # 上次游戏内鼠标位置（脚本内跟踪，跨 click 连续）

def wait(a=0.4, b=0.7):
    """带扰动的等待（秒）"""
    time.sleep(random.uniform(a, b))

def jitter_pt(x, y, r=3):
    return x + random.randint(-r, r), y + random.randint(-r, r)

def move_trace(hwnd, x0, y0, x1, y1):
    """二次贝塞尔轨迹：向上抛物线弧度，smoothstep 缓动，步数更多更顺滑。"""
    dist = abs(x1 - x0) + abs(y1 - y0)
    steps = max(8, min(24, int(dist / 40) + random.randint(4, 8)))
    mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    # 向上弧度：控制点固定在中点上方（屏幕 y 向下，cy 取小），水平带轻微随机
    arc = max(10, int(dist / 4))
    cx = mx + random.uniform(-arc * 0.3, arc * 0.3)
    cy = my - arc * random.uniform(0.7, 1.2)
    for i in range(1, steps + 1):
        t = i / steps
        t = t * t * (3 - 2 * t)  # smoothstep: 两端慢中间快
        u = 1 - t
        x = u * u * x0 + 2 * u * t * cx + t * t * x1
        y = u * u * y0 + 2 * u * t * cy + t * t * y1
        lp = (int(y) << 16) | (int(x) & 0xFFFF)
        ctypes.windll.user32.SendMessageW(hwnd, 0x0200, 0, lp)
        time.sleep(random.uniform(0.005, 0.012))
    lp = (int(y1) << 16) | (int(x1) & 0xFFFF)
    ctypes.windll.user32.SendMessageW(hwnd, 0x0200, 0, lp)

def click(hwnd, x, y, jitter=3):
    """带抖动+轨迹的点击。jitter=0 可关闭位置抖动。"""
    global _last
    tx, ty = jitter_pt(x, y, jitter)
    if _last is None:
        # 首次：从目标附近随机起点飞入，避免"瞬移"
        x0, y0 = tx + random.randint(-70, 70), ty + random.randint(-70, 70)
        move_trace(hwnd, x0, y0, tx, ty)
    else:
        move_trace(hwnd, _last[0], _last[1], tx, ty)
    _last = (tx, ty)
    lp = (ty << 16) | (tx & 0xFFFF)
    ctypes.windll.user32.SendMessageW(hwnd, 0x0201, 0, lp)
    time.sleep(random.uniform(0.02, 0.06))
    ctypes.windll.user32.SendMessageW(hwnd, 0x0202, 0, lp)

def reset():
    global _last
    _last = None
