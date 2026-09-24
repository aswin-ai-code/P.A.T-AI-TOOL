import os


class FileTools:

    def list_files(self):
        items = os.listdir()
        files = [item for item in items if os.path.isfile(item)]

        if not files:
            return "No files found."

        return "Files:\n" + "\n".join(f"- {file}" for file in files)

    def list_folders(self):
        items = os.listdir()
        folders = [item for item in items if os.path.isdir(item)]

        if not folders:
            return "No folders found."

        return "Folders:\n" + "\n".join(f"- {folder}" for folder in folders)

    def file_count(self):
        items = os.listdir()
        count = sum(1 for item in items if os.path.isfile(item))
        return f"There are {count} files in the current directory."

    def folder_count(self):
        items = os.listdir()
        count = sum(1 for item in items if os.path.isdir(item))
        return f"There are {count} folders in the current directory."
