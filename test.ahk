#Include <WebView2\WebView2>

#Include './Kits/Kits.ahk'

main := Gui()
main.OnEvent('Close', (*) => (wvc := wv := 0))
main.Show(Format('w{} h{}', A_ScreenWidth * 0.6, A_ScreenHeight * 0.6))

wvc := WebView2.CreateControllerAsync(main.Hwnd).await2()
wv := wvc.CoreWebView2

if _kits.CheckPort('8080') {
    wv.Navigate("http://localhost:8080")
    wv.OpenDevToolsWindow()
    wv.AddHostObjectToScript('ahk', { str: 'http://localhost:8080', func: MsgBox })
}
else {
    wv.Navigate("file:///" A_ScriptDir "\gui\dist\index.html")
    wv.AddHostObjectToScript('ahk', { str: "file:///" A_ScriptDir "\gui\dist\index.html", func: MsgBox })
}