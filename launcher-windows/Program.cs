using Microsoft.Web.WebView2.WinForms;
using System;
using System.IO;
using System.Reflection;
using System.Windows.Forms;

namespace RostLangLauncher;
internal static class Program
{
    [STAThread]
    static void Main()
    {
        ApplicationConfiguration.Initialize();
        Application.Run(new LauncherForm());
    }
}
public sealed class LauncherForm : Form
{
    private readonly WebView2 view = new() { Dock = DockStyle.Fill };
    public LauncherForm()
    {
        Text = "RostLang Launcher";
        Width = 1200; Height = 820; MinimumSize = new System.Drawing.Size(760, 560);
        Controls.Add(view);
        Shown += async (_, _) =>
        {
            try
            {
                var root = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "RostLang", "launcher");
                Directory.CreateDirectory(root);
                foreach (var name in new[] { "index.html", "style.css", "runtime.js", "app.js" })
                {
                    using var input = Assembly.GetExecutingAssembly().GetManifestResourceStream("RostLauncher." + name)
                        ?? throw new FileNotFoundException("Missing embedded launcher asset: " + name);
                    using var output = File.Create(Path.Combine(root, name));
                    await input.CopyToAsync(output);
                }
                await view.EnsureCoreWebView2Async();
                view.CoreWebView2.Navigate(new Uri(Path.Combine(root, "index.html")).AbsoluteUri);
            }
            catch (Exception ex) { MessageBox.Show("WebView2 could not start. Install Microsoft Edge WebView2 Runtime.\n\n" + ex.Message, "RostLang"); }
        };
    }
}