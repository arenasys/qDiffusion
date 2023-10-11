using System;
using System.Windows.Forms;

namespace qDiffusion
{
    partial class Dialog
    {
        private Label label;
        private ProgressBar progressBar;

        delegate void SetLabelCallback(string value);
        public void SetLabel(string value)
        {
            if (this.label.InvokeRequired)
            {
                SetLabelCallback d = new SetLabelCallback(SetLabel);
                this.Invoke(d, new object[] { value });
            }
            else
            {
                this.label.Text = value;
            }
        }

        delegate void SetProgressCallback(int value);

        public void SetProgress(int value)
        {
            if (this.label.InvokeRequired)
            {
                SetProgressCallback d = new SetProgressCallback(SetProgress);
                this.Invoke(d, new object[] { value });
            }
            else
            {
                this.progressBar.Value = Math.Min(100, value + 1);
                this.progressBar.Value = value;
            }
        }

        delegate void DoCloseCallback();

        public void DoClose()
        {
            if (this.label.InvokeRequired)
            {
                DoCloseCallback d = new DoCloseCallback(DoClose);
                this.Invoke(d, new object[] { });
            }
            else
            {
                this.Close();
            }
        }

        private System.ComponentModel.IContainer components = null;

        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.label = new System.Windows.Forms.Label();
            this.progressBar = new System.Windows.Forms.ProgressBar();
            this.SuspendLayout();
            // 
            // label
            // 
            this.label.AutoSize = true;
            this.label.Font = new System.Drawing.Font("Segoe UI", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(0)));
            this.label.Location = new System.Drawing.Point(12, 9);
            this.label.Name = "label";
            this.label.Size = new System.Drawing.Size(16, 15);
            this.label.TabIndex = 0;
            this.label.Text = "...";
            // 
            // progressBar
            // 
            this.progressBar.Location = new System.Drawing.Point(12, 30);
            this.progressBar.Name = "progressBar";
            this.progressBar.Size = new System.Drawing.Size(210, 23);
            this.progressBar.TabIndex = 1;
            // 
            // Dialog
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(234, 62);
            this.Controls.Add(this.progressBar);
            this.Controls.Add(this.label);
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedSingle;
            this.MaximizeBox = false;
            this.MinimizeBox = false;
            this.Name = "Dialog";
            this.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
            this.Text = "qDiffusion";
            this.ResumeLayout(false);
            this.PerformLayout();

        }

        #endregion
    }
}

