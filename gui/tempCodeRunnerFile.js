const { K } = require('win32-api');
const koffi = require('koffi');

// 加载 Windows 用户32 API
const user32 = K.load('user32');

// 找到 FindWindowA 函数（新版用法）
const FindWindowA = user32.func('HWND FindWindowA(LPCSTR lpClassName, LPCSTR lpWindowName)');
const IsWindow = user32.func('BOOL IsWindow(HWND hWnd)');
const GetWindowTextA = user32.func('int GetWindowTextA(HWND hWnd, LPSTR lpString, int nMaxCount)');

/**
 * 根据窗口类名获取窗口句柄 HWND
 * @param {string} className 窗口类名
 * @returns {number|null} 窗口句柄，找不到返回 null
 */
function getHandleByClassName(className) {
    const hwnd = FindWindowA(className, null);
    return hwnd && IsWindow(hwnd) ? hwnd : null;
}

// ================= 使用示例 =================
const TARGET_CLASS = 'Diablo II'; // 你要查找的窗口类名
const hwnd = getHandleByClassName(TARGET_CLASS);

if (hwnd) {
    console.log('✅ 找到窗口！');
    console.log('窗口类名:', TARGET_CLASS);
    console.log('窗口句柄(HWND):', hwnd, `(0x${hwnd.toString(16).toUpperCase()})`);

    // 获取窗口标题
    const buf = Buffer.alloc(256);
    GetWindowTextA(hwnd, buf, 256);
    const title = buf.toString('utf8').replace(/\0+/g, '');
    console.log('窗口标题:', title);
} else {
    console.log('❌ 未找到对应类名的窗口');
}