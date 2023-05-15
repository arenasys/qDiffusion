package main

import (
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"

	"github.com/hairyhenderson/go-which"
	"github.com/schollz/progressbar/v3"
	"github.com/walle/targz"
)

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
		python = "python"
		if which.Which("python") == "" {
			python = ".\\python\\python.exe"
			if !exists(".\\python") {
				fmt.Println("DOWNLOADING PYTHON")
				err := download("python-3.10.11.tar.gz", "https://github.com/indygreg/python-build-standalone/releases/download/20230507/cpython-3.10.11+20230507-x86_64-pc-windows-msvc-shared-install_only.tar.gz")
				if err != nil {
					fmt.Println(err)
					return
				}
				fmt.Println("EXTRACTING PYTHON")
				err = targz.Extract("python-3.10.11.tar.gz", ".")
				if err != nil {
					fmt.Println(err)
					return
				}
			}
		}
	}

	if proc, err := start(python, "source\\launch.py"); err == nil {
		proc.Wait()
	}
}
