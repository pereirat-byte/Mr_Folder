# -*- coding: utf-8 -*-
"""
Mr Folder
- TWIMExtract folder reorganizer
- CIUSuite analyzed-data folder generator

The TWIMExtract reorganizer groups immediate subfolders by removing their final
two characters (for example, Sample_1_5 -> Sample_1). It moves the contents
of each source folder into the corresponding grouped folder. It does not
overwrite existing files. Empty source folders are removed only after their
contents have been moved successfully.
"""

from pathlib import Path
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox


def choose_directory(title):
    """Open a directory picker and return a Path, or None if cancelled."""
    selected = filedialog.askdirectory(parent=root, title=title)
    return Path(selected) if selected else None


def twim_reorganizer_function():
    """Group TWIMExtract output folders and move their contents safely."""
    root_folder = choose_directory("Select the TWIMExtract output directory")
    if root_folder is None:
        return

    if not root_folder.is_dir():
        messagebox.showerror("Invalid directory", "The selected path is not a directory.")
        return

    source_folders = sorted(
        (p for p in root_folder.iterdir() if p.is_dir()),
        key=lambda p: p.name.lower()
    )

    if not source_folders:
        messagebox.showinfo("Nothing to do", "No subfolders were found in the selected directory.")
        return

    # Match the original naming rule, but avoid silently truncating names
    # that do not have the expected two-character suffix.
    invalid_names = [p.name for p in source_folders if len(p.name) <= 2]
    if invalid_names:
        messagebox.showerror(
            "Unexpected folder name",
            "These folder names are too short to apply the two-character grouping rule:\n\n"
            + "\n".join(invalid_names)
        )
        return

    groups = {}
    for source in source_folders:
        group_name = source.name[:-2]
        groups.setdefault(group_name, []).append(source)

    # Build a preview and require explicit confirmation before moving anything.
    preview_lines = []
    for group_name, sources in groups.items():
        preview_lines.append(f"{group_name}/  <-  " + ", ".join(p.name for p in sources))

    confirmed = messagebox.askyesno(
        "Confirm reorganization",
        "The following folders will be grouped. Their contents will be moved; "
        "existing destination items will not be overwritten.\n\n"
        + "\n".join(preview_lines)
        + "\n\nContinue?"
    )
    if not confirmed:
        return

    errors = []
    moved_count = 0

    for group_name, sources in groups.items():
        destination = root_folder / group_name

        # If a source folder is itself the destination, do not try to move it
        # into itself (this can occur with unusual folder names).
        if any(source.resolve() == destination.resolve() for source in sources):
            errors.append(f"Skipped group '{group_name}': destination is also a source folder.")
            continue

        try:
            destination.mkdir(exist_ok=True)
        except OSError as exc:
            errors.append(f"Could not create '{destination}': {exc}")
            continue

        for source_folder in sources:
            # Move each immediate child, preserving subdirectories.
            # Refuse collisions rather than overwriting user data.
            try:
                children = list(source_folder.iterdir())
            except OSError as exc:
                errors.append(f"Could not read '{source_folder}': {exc}")
                continue

            for item in children:
                target = destination / item.name
                if target.exists():
                    errors.append(
                        f"Name collision: '{item}' was not moved because '{target}' already exists."
                    )
                    continue
                try:
                    shutil.move(str(item), str(target))
                    moved_count += 1
                except OSError as exc:
                    errors.append(f"Could not move '{item}' to '{target}': {exc}")

            # Remove only if empty. Path.rmdir() cannot remove a nonempty folder.
            try:
                source_folder.rmdir()
            except OSError:
                # Preserve any source folder containing items that were not moved.
                pass

    summary = f"Reorganization finished. Moved {moved_count} item(s)."
    if errors:
        details = "\n\n".join(errors[:15])
        if len(errors) > 15:
            details += f"\n\n...and {len(errors) - 15} more issue(s)."
        messagebox.showwarning("Completed with issues", summary + "\n\n" + details)
    else:
        messagebox.showinfo("Complete", summary)


def ciu_generator_function():
    """Create the standard CIUSuite analyzed-data folder structure."""
    data_folder = choose_directory("Select the data directory")
    if data_folder is None:
        return

    if not data_folder.is_dir():
        messagebox.showerror("Invalid directory", "The selected path is not a directory.")
        return

    folder_names = sorted(
        (p.name for p in data_folder.iterdir() if p.is_dir()),
        key=str.lower
    )

    if not folder_names:
        messagebox.showinfo("Nothing to do", "No subfolders were found in the selected data directory.")
        return

    desktop_path = Path.home() / "Desktop"
    analyzed_data_path = desktop_path / "Analyzed data"

    if analyzed_data_path.exists():
        messagebox.showerror(
            "Output already exists",
            f"The folder already exists:\n{analyzed_data_path}\n\n"
            "To prevent accidental changes, nothing was created. Rename or move "
            "the existing folder, then try again."
        )
        return

    ciu_subfolders = ["Average", "CIU50 and Features", "Plots"]

    # Create the requested structure directly under each detected folder.
    try:
        analyzed_data_path.mkdir(parents=True, exist_ok=False)
        for folder_name in folder_names:
            for subfolder in ciu_subfolders:
                (analyzed_data_path / folder_name / subfolder).mkdir(
                    parents=True, exist_ok=True
                )
    except OSError as exc:
        messagebox.showerror(
            "Folder creation error",
            f"An error occurred while creating the folder structure:\n{exc}\n\n"
            f"Check the partially created folder:\n{analyzed_data_path}"
        )
        return

    messagebox.showinfo(
        "Complete",
        f"CIUSuite folder generation complete.\n\nCreated:\n{analyzed_data_path}"
    )


# Initialize the GUI only after both callback functions have been defined.
root = tk.Tk()
root.title("Mr Folder")
root.geometry("360x190")
root.resizable(False, False)

title_label = tk.Label(root, text="Mr Folder", font=("Arial", 16, "bold"))
title_label.pack(pady=18)

button1 = tk.Button(
    root,
    text="CIU Folder Generator",
    command=ciu_generator_function,
    width=32
)
button1.pack(pady=6)

button2 = tk.Button(
    root,
    text="TWIMExtract Folder Reorganizer",
    command=twim_reorganizer_function,
    width=32
)
button2.pack(pady=6)

root.mainloop()
