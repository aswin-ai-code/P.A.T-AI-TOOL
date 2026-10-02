import os
import subprocess
import webbrowser


class AppTools:
    def open_calculator(self):
        subprocess.Popen("calc.exe")
        return "Calculator opened."

    def open_notepad(self):
        subprocess.Popen("notepad.exe")
        return "Notepad opened."

    def open_browser(self):
        webbrowser.open("https://www.google.com")
        return "Browser opened."

    def open_youtube(self):
        webbrowser.open("https://www.youtube.com")
        return "YouTube opened."

    def open_google(self):
        webbrowser.open("https://www.google.com")
        return "Google opened."

    def current_directory(self):
        return f"Current directory: {os.getcwd()}"

    def clear_screen(self):
        os.system("cls")
        return "Screen cleared."

    def close_calculator(self):
        subprocess.run(
            ["taskkill", "/IM", "CalculatorApp.exe", "/F"],
            capture_output=True,
        )
        return "Calculator closed."

    def close_notepad(self):
        subprocess.run(
            ["taskkill", "/IM", "notepad.exe", "/F"],
            capture_output=True,
        )
        return "Notepad closed."

    def close_browser(self):
        return "Browser close control will be added safely."

    def show_desktop(self):
        subprocess.run(
            [
                "powershell",
                "-Command",
                "(New-Object -ComObject Shell.Application).MinimizeAll()",
            ]
        )
        return "Desktop shown."

    def minimize_window(self):
        return "Window minimize control will be added."

    def maximize_window(self):
        return "Window maximize control will be added."

    def lock_computer(self):
        subprocess.run(
            ["rundll32.exe", "user32.dll,LockWorkStation"]
        )
        return "Computer locked."

    def open_file(self):
        os.startfile(os.getcwd())
        return "File location opened."

    def open_folder(self):
        os.startfile(os.getcwd())
        return "Folder opened."

    def open_specific_file(self, target):
        if not target:
            return "File name சொல்லவில்லை."

        file_path = os.path.abspath(target)

        if not os.path.isfile(file_path):
            return f"File கிடைக்கவில்லை: {target}"

        os.startfile(file_path)
        return f"{target} opened."

    def open_specific_folder(self, target):
        if not target:
            return "Folder name சொல்லவில்லை."

        folder_path = os.path.abspath(target)

        if not os.path.isdir(folder_path):
            return f"Folder கிடைக்கவில்லை: {target}"

        os.startfile(folder_path)
        return f"{target} folder opened."

    def close_specific_folder(self, target):
        if not target:
            return "Folder name சொல்லவில்லை."

        folder_path = os.path.abspath(target)

        if not os.path.isdir(folder_path):
            return f"Folder கிடைக்கவில்லை: {target}"

        folder_name = os.path.basename(os.path.normpath(folder_path))

        powershell_script = f"""
$shell = New-Object -ComObject Shell.Application
$closed = $false

foreach ($window in $shell.Windows()) {{
    try {{
        $path = $window.Document.Folder.Self.Path

        if ($path -eq '{folder_path.replace("'", "''")}') {{
            $window.Quit()
            $closed = $true
        }}
    }}
    catch {{
    }}
}}

if ($closed) {{
    Write-Output "CLOSED"
}}
else {{
    Write-Output "NOT_FOUND"
}}
"""

        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                powershell_script,
            ],
            capture_output=True,
            text=True,
        )

        output = result.stdout.strip()

        if output == "CLOSED":
            return f"{folder_name} folder closed."

        return f"{folder_name} folder is not currently open."