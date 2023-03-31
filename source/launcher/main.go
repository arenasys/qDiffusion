package main

import (
	"os"
	"os/exec"
)

func Start(args ...string) (p *os.Process, err error) {
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

func main() {
	if proc, err := Start(".\\venv\\Scripts\\pythonw", "source\\main.py"); err == nil {
		proc.Wait()
	}
}
