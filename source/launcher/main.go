package main

import (
	"os"
	"os/exec"
)

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
	}

	if proc, err := start(python, "source\\launch.py"); err == nil {
		proc.Wait()
	}
}
