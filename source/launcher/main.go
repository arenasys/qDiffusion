package main

import (
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"syscall"
	"time"

	"github.com/schollz/progressbar/v3"
	"github.com/walle/targz"
	"golang.org/x/sys/windows"
)

var attached bool = false

func log(err error) {
	attach()
	msg := fmt.Sprintf("LAUNCHER %s\n%s\n", time.Now().Local().String(), err.Error())
	fmt.Println(msg)
	f, _ := os.OpenFile("crash.log", os.O_APPEND|os.O_WRONLY|os.O_CREATE, 0644)
	f.WriteString(msg + "\n")
	f.Close()
	fmt.Println("TRACEBACK SAVED: crash.log")
	time.Sleep(5 * time.Second)
}

func attach() {
	if attached {
		return
	}
	proc := syscall.MustLoadDLL("kernel32.dll").MustFindProc("AllocConsole")
	proc.Call()
	out, _ := windows.GetStdHandle(windows.STD_OUTPUT_HANDLE)
	outF := os.NewFile(uintptr(out), "/dev/stdout")
	windows.SetStdHandle(windows.STD_OUTPUT_HANDLE, windows.Handle(outF.Fd()))
	os.Stdout = outF
	os.Stderr = outF
	attached = true
}

func download(path, url string) error {
	req, _ := http.NewRequest("GET", url, nil)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return err
	}

	defer resp.Body.Close()

	f, _ := os.OpenFile(path, os.O_CREATE|os.O_WRONLY, 0644)
	defer f.Close()

	bar := progressbar.DefaultBytes(
		resp.ContentLength,
		path,
	)

	io.Copy(io.MultiWriter(f, bar), resp.Body)
	return nil
}

func start(args ...string) (p *os.Process, err error) {
	if args[0], err = exec.LookPath(args[0]); err == nil {
		var procAttr os.ProcAttr
		procAttr.Files = []*os.File{os.Stdin,
			os.Stdout, os.Stderr}
		p, err := os.StartProcess(args[0], args, &procAttr)
		if err == nil {
			return p, nil
		}
	}
	return nil, err
}

func exists(path string) bool {
	if stat, err := os.Stat(path); err == nil && stat.IsDir() {
		return true
	}
	return false
}

func main() {
	python := ".\\venv\\Scripts\\pythonw"
	if !exists(".\\venv") {
		python = ".\\python\\python.exe"
		if !exists(".\\python") {
			attach()
			fmt.Println("DOWNLOADING PYTHON...")
			err := download("python-3.10.11.tar.gz", "https://github.com/indygreg/python-build-standalone/releases/download/20230507/cpython-3.10.11+20230507-x86_64-pc-windows-msvc-shared-install_only.tar.gz")
			if err != nil {
				log(err)
				return
			}
			fmt.Println("EXTRACTING PYTHON...")
			err = targz.Extract("python-3.10.11.tar.gz", ".")
			if err != nil {
				log(err)
				return
			}
			os.Remove("python-3.10.11.tar.gz")
		}
	}

	if proc, err := start(python, "source\\launch.py"); err == nil {
		proc.Wait()
	} else {
		log(err)
	}
}
