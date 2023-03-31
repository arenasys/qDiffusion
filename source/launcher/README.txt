go get github.com/akavel/rsrc
rsrc -ico icon.ico
go build -ldflags -H=windowsgui
cp qDiffusion.exe ..\..\qDiffusion.exe