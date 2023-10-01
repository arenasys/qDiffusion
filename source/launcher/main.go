package main

import (
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
	"time"
	"unsafe"

	"github.com/ncruces/zenity"
	"github.com/walle/targz"
)

var python_file string = "python-3.10.11.tar.gz"
var python_url string = "https://github.com/indygreg/python-build-standalone/releases/download/20230507/cpython-3.10.11+20230507-x86_64-pc-windows-msvc-shared-install_only.tar.gz"

var pyqt_file string = "PyQt5-5.15.7-cp37-abi3-win_amd64.whl"
var pyqt_url string = "https://files.pythonhosted.org/packages/bd/85/31a12415765acb48fddac3e207cfffcbbae826fe194cf1d92179d8872f59/PyQt5-5.15.7-cp37-abi3-win_amd64.whl"

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

type ProgressWriter struct {
	dlg     zenity.ProgressDialog
	current int64
	total   int64
	last    int
}

func (p *ProgressWriter) Write(data []byte) (n int, err error) {
	n = len(data)
	p.current += int64(n)
	var progress = int(100.0 * float64(p.current) / float64(p.total))
	if progress != p.last {
		p.dlg.Value(min(99, progress+1))
		if err = p.dlg.Value(min(99, progress)); err != nil {
			return n, fmt.Errorf("abort")
		}
		p.last = progress
	}
	return n, nil
}

func ErrorPopup(err string) {
	zenity.Error(err, zenity.Title("Error occurred"), zenity.ErrorIcon)
	fmt.Fprintln(os.Stderr, err)
	os.Exit(-1)
}

func Log(err error) {
	if err.Error() == "abort" {
		return
	}
	f, _ := os.OpenFile("crash.log", os.O_APPEND|os.O_WRONLY|os.O_CREATE, 0644)
	f.WriteString(fmt.Sprintf("LAUNCHER %s\n%s\n\n", time.Now().Local().String(), err.Error()))
	f.Close()
	ErrorPopup(fmt.Sprintf("%s.\n\nError saved to crash.log", err.Error()))
}

func Download(path, url string, dlg zenity.ProgressDialog) error {
	req, _ := http.NewRequest("GET", url, nil)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return err
	}

	defer resp.Body.Close()

	f, _ := os.OpenFile(path, os.O_CREATE|os.O_WRONLY, 0644)
	defer f.Close()

	bar := ProgressWriter{}
	bar.dlg = dlg
	bar.total = resp.ContentLength

	_, err = io.Copy(io.MultiWriter(f, &bar), resp.Body)
	return err
}

func Run(args ...string) (err error) {
	if args[0], err = exec.LookPath(args[0]); err == nil {
		r, w, _ := os.Pipe()
		var procAttr os.ProcAttr
		procAttr.Files = []*os.File{os.Stdin, os.Stdout, w}
		procAttr.Env = os.Environ()
		p, err := os.StartProcess(args[0], args, &procAttr)
		if err == nil {
			var status *os.ProcessState
			status, err = p.Wait()
			w.Close()
			if err != nil {
				return err
			}
			if !status.Success() {
				builder := new(strings.Builder)
				io.Copy(builder, r)
				return fmt.Errorf(builder.String())
			}
			return nil
		}
	}
	return err
}

func Launch(args ...string) (p *os.Process, err error) {
	if args[0], err = exec.LookPath(args[0]); err == nil {
		var procAttr os.ProcAttr
		procAttr.Files = []*os.File{os.Stdin, os.Stdout, os.Stderr}
		procAttr.Env = os.Environ()
		return os.StartProcess(args[0], args, &procAttr)
	}
	return nil, err
}

func Exists(path string) bool {
	if stat, err := os.Stat(path); err == nil && stat.IsDir() {
		return true
	}
	return false
}

func WriteTest() error {
	f, err := os.OpenFile("crash.log", os.O_APPEND|os.O_WRONLY|os.O_CREATE, 0644)
	if err != nil {
		return err
	}
	_, err = f.WriteString("POKE" + "\n")
	if err != nil {
		return err
	}
	f.Close()
	return nil
}

func SetCurrentProcessExplicitAppUserModelID(appID string) bool {
	shell32 := syscall.NewLazyDLL("shell32.dll")
	procSetCurrentProcessExplicitAppUserModelID := shell32.NewProc("SetCurrentProcessExplicitAppUserModelID")

	wAppID, err := syscall.UTF16PtrFromString(appID)
	if err != nil {
		return false
	}

	result, _, _ := procSetCurrentProcessExplicitAppUserModelID.Call(uintptr(unsafe.Pointer(wAppID)))
	return result == 0
}

func main() {
	exe, _ := os.Executable()
	exe_dir := filepath.Dir(exe)
	os.Chdir(exe_dir)

	// Set early (also set in main.py) to avoid flickering
	SetCurrentProcessExplicitAppUserModelID("arenasys.qdiffusion.v1")

	args := os.Args[1:]
	if len(args) >= 2 {
		if args[0] == "-e" {
			ErrorPopup(args[1])
			return
		}
	}

	if !Exists(".\\source") {
		ErrorPopup("Missing sources. Please extract the ZIP archive.")
		return
	}

	var dlg zenity.ProgressDialog = nil

	if !Exists(".\\python") {
		err := WriteTest()
		if err != nil {
			ErrorPopup("Write failed. Please extract the ZIP archive to a folder with write permissions.")
			return
		}

		dlg, _ = zenity.Progress(zenity.Title("qDiffusion"), zenity.WindowIcon(exe))

		dlg.Text("Downloading Python")
		dlg.Value(0)
		err = Download(python_file, python_url, dlg)
		if err != nil {
			Log(err)
			return
		}

		dlg.Text("Installing Python")
		err = targz.Extract(python_file, ".")
		if err != nil {
			Log(err)
			return
		}
		os.Remove(python_file)
	}

	python := ".\\python\\pythonw.exe"
	if !Exists(".\\venv") {
		if dlg == nil {
			dlg, _ = zenity.Progress(zenity.Title("qDiffusion"), zenity.WindowIcon(exe))
		}

		dlg.Text("Creating Environment")
		dlg.Value(99)
		if err := Run(python, "-m", "venv", "venv"); err != nil {
			Log(err)
			return
		}
	}

	// Activate VENV
	os.Setenv("PATH", filepath.Join(exe_dir, "venv", "Scripts")+";"+os.Getenv("PATH"))
	os.Setenv("VIRTUAL_ENV", filepath.Join(exe_dir, "venv"))
	os.Unsetenv("PYTHONHOME")
	python = ".\\venv\\Scripts\\pythonw.exe"

	// Set AMD variables
	os.Setenv("HSA_OVERRIDE_GFX_VERSION", "10.3.0")
	os.Setenv("MIOPEN_LOG_LEVEL", "4")

	// Cleanup Qt variables
	for _, entry := range os.Environ() {
		key := strings.Split(entry, "=")[0]
		if strings.HasPrefix(key, "QT") {
			os.Unsetenv(key)
		}
	}

	if !Exists(".\\venv\\Lib\\site-packages\\PyQt5") {
		if dlg == nil {
			dlg, _ = zenity.Progress(zenity.Title("qDiffusion"), zenity.WindowIcon(exe))
		}

		dlg.Text("Downloading PyQT5")
		dlg.Value(0)
		err := Download(pyqt_file, pyqt_url, dlg)
		if err != nil {
			Log(err)
			return
		}

		dlg.Text("Installing PyQT5")
		if err := Run(python, "-m", "pip", "install", pyqt_file); err != nil {
			Log(err)
			return
		}
		os.Remove(pyqt_file)
	}

	if dlg != nil {
		dlg.Close()
	}

	if proc, err := Launch(python, "source\\main.py"); err != nil {
		ErrorPopup(err.Error())
	} else {
		proc.Release()
	}
}
