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
