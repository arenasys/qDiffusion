using System;
using System.Threading;
using System.IO;
using System.Net;
using System.Reflection;
using System.Runtime.InteropServices;
using System.ComponentModel;
using System.Text;
using System.IO.Compression;
using System.Collections;
using System.Diagnostics;
using System.Windows.Forms;
using System.Drawing;
using System.Linq;
using Microsoft.Win32;

namespace qDiffusion
{
    class Worker
    {
        [DllImport("shell32.dll", SetLastError = true)]
        static extern void SetCurrentProcessExplicitAppUserModelID([MarshalAs(UnmanagedType.LPWStr)] string AppID);

        private Dialog progress;

        private void LaunchProgress()
        {
            if (progress == null)
            {
                new Thread(delegate ()
                {
                    progress = new Dialog();
                    progress.Icon = Icon.ExtractAssociatedIcon(Assembly.GetExecutingAssembly().Location);
                    Application.Run(progress);
                }).Start();

                while (progress == null)
                {
                    Thread.Sleep(1); //SPIN!!
                }
            }
        }

        private void LaunchError(string error)
        {
            MessageBox.Show(error, "Error occurred", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }

        static void RegisterProtocol(string exe)
        {
            RegistryKey key = Registry.CurrentUser.OpenSubKey(@"Software\Classes\qDiffusion");

            bool replace = false;
            if (key != null)
            {
                replace = true;
                var command = key.OpenSubKey(@"shell\open\command");
                if (command != null)
                {
                    string value = (string)command.GetValue(string.Empty);
                    if (value != null && value.Contains(exe))
                    {
                        replace = false;
                    }
                }
            }

            if (replace)
            {
                Registry.CurrentUser.DeleteSubKeyTree(@"Software\Classes\qDiffusion");
                key = null;
            }

            if (key == null)
            {
                key = Registry.CurrentUser.CreateSubKey(@"Software\Classes\qDiffusion");
                key.SetValue(string.Empty, "URL:qDiffusion");
                key.SetValue("URL Protocol", string.Empty);

                var icon = key.CreateSubKey("DefaultIcon");
                icon.SetValue(string.Empty, "\"" + exe + "\",1");
                icon.Close();

                var command = key.CreateSubKey(@"shell\open\command");
                command.SetValue(string.Empty, "\"" + exe + "\" \"%1\"");
                command.Close();
            }

            key.Close();
        }

        private void HandleDownloadComplete(object sender, AsyncCompletedEventArgs args)
        {
            lock (args.UserState)
            {
                Monitor.Pulse(args.UserState);
            }
        }

        private void HandleDownloadProgress(object sender, DownloadProgressChangedEventArgs args)
        {
            progress?.SetProgress(Math.Min(99, args.ProgressPercentage));
        }

        private void Download(string url, string filename)
        {
            using (WebClient wc = new WebClient())
            {
                wc.DownloadProgressChanged += HandleDownloadProgress;
                wc.DownloadFileCompleted += HandleDownloadComplete;

                var syncObject = new object();
                lock (syncObject)
                {
                    wc.DownloadFileAsync(new Uri(url), filename, syncObject);
                    Monitor.Wait(syncObject);
                }
            }
        }

        public static string GetString(byte[] buffer, int length)
        {
            return Encoding.ASCII.GetString(buffer, 0, length).Split('\0')[0];
        }

        public static void ExtractTarGz(string filename, string outputDir)
        {
            void ReadExactly(Stream stream, byte[] buffer, int count)
            {
                var total = 0;
                while (true)
                {
                    int n = stream.Read(buffer, total, count - total);
                    total += n;
                    if (total == count)
                        return;
                }
            }

            void SeekExactly(Stream stream, byte[] buffer, int count)
            {
                ReadExactly(stream, buffer, count);
            }

            using (var fs = File.OpenRead(filename))
            {
                using (var stream = new GZipStream(fs, CompressionMode.Decompress))
                {
                    var buffer = new byte[1024];
                    while (true)
                    {
                        ReadExactly(stream, buffer, 100);
                        var name = Encoding.ASCII.GetString(buffer, 0, 100).Split('\0')[0];
                        if (String.IsNullOrWhiteSpace(name))
                            break;

                        SeekExactly(stream, buffer, 24);

                        ReadExactly(stream, buffer, 12);
                        var sizeString = Encoding.ASCII.GetString(buffer, 0, 12).Split('\0')[0];
                        var size = Convert.ToInt64(sizeString, 8);

                        SeekExactly(stream, buffer, 209);

                        ReadExactly(stream, buffer, 155);
                        var prefix = Encoding.ASCII.GetString(buffer, 0, 155).Split('\0')[0];
                        if (!String.IsNullOrWhiteSpace(prefix))
                        {
                            name = prefix + name;
                        }

                        SeekExactly(stream, buffer, 12);

                        var output = Path.GetFullPath(Path.Combine(outputDir, name));
                        if (!Directory.Exists(Path.GetDirectoryName(output)))
                        {
                            Directory.CreateDirectory(Path.GetDirectoryName(output));
                        }
                        using (var outfs = File.Open(output, FileMode.OpenOrCreate, FileAccess.Write))
                        {
                            var total = 0;
                            var next = 0;
                            while (true)
                            {
                                next = Math.Min(buffer.Length, (int)size - total);
                                ReadExactly(stream, buffer, next);
                                outfs.Write(buffer, 0, next);
                                total += next;
                                if (total == size)
                                    break;
                            }
                        }

                        var offset = 512 - ((int)size % 512);
                        if (offset == 512)
                            offset = 0;

                        SeekExactly(stream, buffer, offset);
                    }
                }
            }
        }

        public static string MD5(string input)
        {
            using (System.Security.Cryptography.MD5 md5 = System.Security.Cryptography.MD5.Create())
            {
                byte[] inputBytes = Encoding.ASCII.GetBytes(input);
                byte[] hashBytes = md5.ComputeHash(inputBytes);
                StringBuilder hex = new StringBuilder(hashBytes.Length * 2);
                foreach (byte b in hashBytes)
                {
                    hex.AppendFormat("{0:x2}", b);
                }
                return hex.ToString();
            }
        }

        public static void Run(params string[] args)
        {
            string command = args[0];
            string arguments = string.Join(" ", args, 1, args.Length - 1);

            ProcessStartInfo startInfo = new ProcessStartInfo(command, arguments)
            {
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            Process process = new Process
            {
                StartInfo = startInfo
            };

            try
            {
                process.Start();
                process.WaitForExit();

                if (process.ExitCode != 0)
                {
                    string errorOutput = process.StandardError.ReadToEnd();
                    if (string.IsNullOrEmpty(errorOutput))
                    {
                        errorOutput = process.StandardOutput.ReadToEnd();
                    }
                    throw new Exception(errorOutput);
                }
            }
            catch (Exception ex)
            {
                throw new Exception(ex.Message);
            }
        }

        public static void Launch(params string[] args)
        {
            string command = args[0];
            string arguments = string.Join(" ", args, 1, args.Length - 1);

            ProcessStartInfo startInfo = new ProcessStartInfo(command, arguments)
            {
                UseShellExecute = false,
                RedirectStandardInput = false,
                RedirectStandardOutput = false,
                RedirectStandardError = false
            };

            Process process = new Process
            {
                StartInfo = startInfo
            };

            process.Start();
        }
        public void Work(string[] args)
        {
            var exe = Assembly.GetEntryAssembly().Location;
            var exe_dir = Path.GetDirectoryName(exe);
            Directory.SetCurrentDirectory(exe_dir);

            var app_user_model_id = "arenasys.qdiffusion." + MD5(exe);
            SetCurrentProcessExplicitAppUserModelID(app_user_model_id);

            if (args.Length >= 2 && args[0] == "-e")
            {
                LaunchError(args[1]);
                return;
            }

            if (!Directory.Exists("source"))
            {
                LaunchError("Missing sources. Please extract the ZIP archive.");
                return;
            }

            if (!Directory.Exists("python"))
            {
                try
                {
                    using (FileStream fs = File.Create(Path.GetRandomFileName(), 1, FileOptions.DeleteOnClose)) { }
                }
                catch
                {
                    LaunchError("Write failed. Please extract the ZIP archive to a folder with write permissions.");
                    return;
                }

                LaunchProgress();
                progress?.SetLabel("Downloading Python");

                var python_file = "python-3.10.11.tar.gz";
                var python_url = "https://github.com/arenasys/binaries/releases/download/v1/cpython-3.10.11+20230507-x86_64-pc-windows-msvc-shared-install_only.tar.gz";
                Download(python_url, python_file);

                progress?.SetLabel("Installing Python");
                ExtractTarGz(python_file, ".");

                File.Delete(python_file);
            }

            foreach (DictionaryEntry de in Environment.GetEnvironmentVariables())
            {
                var key = (string)de.Key;
                if (key.StartsWith("QT") || key.StartsWith("PIP") || key.StartsWith("PYTHON"))
                {
                    Environment.SetEnvironmentVariable(key, null);
                }
            }

            var python = ".\\python\\pythonw.exe";

            if (!Directory.Exists("venv"))
            {
                LaunchProgress();
                progress?.SetLabel("Creating Environment");
                progress?.SetProgress(99);

                try
                {
                    Run(python, "-m", "venv", "venv");
                }
                catch (Exception ex)
                {
                    LaunchError(ex.Message);
                    return;
                }
            }

            // Activate VENV
            var path = Environment.GetEnvironmentVariable("PATH");
            Environment.SetEnvironmentVariable("PATH", Path.Combine(exe_dir, "venv", "Scripts") + ";" + path);
            Environment.SetEnvironmentVariable("VIRTUAL_ENV", Path.Combine(exe_dir, "venv"));
            Environment.SetEnvironmentVariable("PIP_CONFIG_FILE", "nul");

            // Register qdiffusion:// protocol handler
            RegisterProtocol(exe);

            python = ".\\venv\\Scripts\\pythonw.exe";

            // Set AMD variables
            Environment.SetEnvironmentVariable("HSA_OVERRIDE_GFX_VERSION", "10.3.0");
            Environment.SetEnvironmentVariable("MIOPEN_LOG_LEVEL", "4");

            if (!Directory.Exists("venv\\Lib\\site-packages\\PyQt5"))
            {
                LaunchProgress();
                progress?.SetLabel("Downloading PyQT5");
                progress?.SetProgress(0);

                var pyqt_file = "PyQt5-5.15.7-cp37-abi3-win_amd64.whl";
                var pyqt_url = "https://github.com/arenasys/binaries/releases/download/v1/PyQt5-5.15.7-cp37-abi3-win_amd64.whl";
                Download(pyqt_url, pyqt_file);

                progress?.SetLabel("Installing PyQT5");

                Run(python, "-m", "pip", "install", pyqt_file);

                File.Delete(pyqt_file);
            }

            progress?.DoClose();

            try
            {
                string[] cmd = { python, "source\\main.py" };
                Launch(cmd.Concat(args).ToArray());
            }
            catch (Exception ex)
            {
                LaunchError(ex.Message);
                return;
            }
        }
    }
    internal static class Program
    {
        [STAThread]
        static void Main(string[] args)
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Worker worker = new Worker();
            worker.Work(args);
        }
    }
}