go build github.com/josephspurrier/goversioninfo/cmd/goversioninfo
.\goversioninfo.exe -icon='icon.ico'
go build -ldflags -H=windowsgui
cp qDiffusion.exe ..\..\qDiffusion.exe