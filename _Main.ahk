#NoTrayIcon

#Include <WebView2\WebView2>
#Include './_AutoInclude.ahk'
#Include './Kits/Kits.ahk'

TraySetIcon("./Img/icon.png")
A_IconTip := "暗黑2工具箱"

injectObj := { fn: ConstructorFn(GetAhkFilesWithoutExt()) }

; || 创建窗口
main := Gui("+OwnDialogs", "暗黑2工具箱")
A_TrayMenu.Delete()
main.Show(Format('w{} h{}', 1070, 740))
wvc := WebView2.CreateControllerAsync(main.Hwnd).await2()
wv := wvc.CoreWebView2

wv.Settings.AreBrowserAcceleratorKeysEnabled := false
wv.Settings.AreDefaultContextMenusEnabled := false
wv.Settings.IsZoomControlEnabled := false

wv.Navigate(getGuiNav())

if FileExist("port.txt")
    wv.OpenDevToolsWindow()

injectObj.webViewController := { switchGuiState: switchGuiState, Hwnd: main.Hwnd }

injectObj.fn.WinActivate := WinActivate
injectObj.fn.DllCall := DllCall
injectObj.fn.WinSetAlwaysOnTop := WinSetAlwaysOnTop
injectObj.fn.RegWrite := RegWrite


; || 注入函数到前端
wv.AddHostObjectToScript('ahk', injectObj)

switchGuiState(flag) {
    main.Opt(flag)
}