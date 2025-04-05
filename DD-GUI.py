import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import re
import os
import signal
from functools import partial
from datetime import datetime

class DDUtilityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DD Utility")
        self.root.configure(bg='#1E1E1E')
        
        # Set window icon
        try:
            icon_path = "/etc/dd_gui/DD_GUI.png"
            if os.path.exists(icon_path):
                img = tk.PhotoImage(file=icon_path)
                self.root.tk.call('wm', 'iconphoto', self.root._w, img)
        except Exception as e:
            print(f"Error loading icon: {e}")

        self.main_frame = tk.Frame(self.root, bg='#1E1E1E')
        self.main_frame.pack(padx=20, pady=20, fill='both', expand=True)

        # Variables
        self.selected_file = None
        self.selected_source_disk = None
        self.selected_destination_disk = None
        self.total_size = 0
        self.task_message = ""
        self.process = None
        self.font = ("Segoe UI", 12, "bold")
        self.disk_selection_font = ("Segoe UI", 14, "bold")
        self.cancelled = False
        self.disk_info = {}

        # Initialize UI
        self.initialize_ui()

    def initialize_ui(self):
        self.clear_ui()
        self.cancelled = False
        
        # Add icon to corner if available
        try:
            icon_path = "/etc/dd_gui/DD_GUI.png"
            if os.path.exists(icon_path):
                img = tk.PhotoImage(file=icon_path)
                icon_label = tk.Label(self.main_frame, image=img, bg='#1E1E1E')
                icon_label.image = img  # Keep reference
                icon_label.pack(pady=10)
        except Exception as e:
            print(f"Error loading corner icon: {e}")

        tk.Label(
            self.main_frame,
            text="Choose DD Task",
            bg='#1E1E1E',
            fg='#FFFFFF',
            font=("Segoe UI", 16, "bold")
        ).pack(pady=20)

        # Button styling
        button_options = {
            'width': 25,
            'font': self.font,
            'bg': '#a5de37',
            'fg': '#000000',
            'relief': 'flat',
            'activebackground': '#8BC34A'
        }

        tasks = [
            ("File to Disk", self.file_to_disk),
            ("Disk to Disk", self.disk_to_disk),
            ("Create Partition Table", self.create_partition_table),
            ("Format Disk/Partition", self.format_disk),
            ("Secure Erase Disk", self.secure_erase),
            ("Create Disk Image", self.create_disk_image)
        ]

        for text, command in tasks:
            tk.Button(
                self.main_frame,
                text=text,
                command=command,
                **button_options
            ).pack(pady=10)

    def clear_ui(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def add_back_button(self):
        tk.Button(
            self.main_frame,
            text="Back",
            command=self.initialize_ui,
            font=self.font,
            bg='#555555',
            fg='#a5de37',
            relief='flat'
        ).pack(pady=10)

    def add_cancel_button(self):
        tk.Button(
            self.main_frame,
            text="Cancel",
            command=self.cancel_operation,
            font=self.font,
            bg='#FF4D00',
            fg='#FFFFFF',
            relief='flat'
        ).pack(pady=10)

    def choose_file(self, title="Select File"):
        try:
            result = subprocess.run(
                ["zenity", "--file-selection", f"--title={title}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception as e:
            print(f"Error opening file manager: {e}")
            return None

    def choose_directory(self, title="Select Directory"):
        try:
            result = subprocess.run(
                ["zenity", "--file-selection", "--directory", f"--title={title}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception as e:
            print(f"Error opening directory selector: {e}")
            return None

    def choose_disk(self, prompt, preselect=None, on_done=None):
        try:
            disk_details = subprocess.check_output(
                ["lsblk", "-dpno", "NAME,SIZE,TYPE,MODEL"]
            ).decode().strip().split("\n")
            
            disk_choices = []
            disk_info = {}
            
            for line in disk_details:
                if line.startswith('/dev/sd') or line.startswith('/dev/mmcblk') or line.startswith('/dev/loop'):
                    parts = line.split()
                    disk_path = parts[0]
                    disk_size = parts[1]
                    disk_type = parts[2]
                    disk_model = ' '.join(parts[3:]) if len(parts) > 3 else 'Unknown'
                    
                    display_name = f"{disk_path} ({disk_size}) - {disk_model}"
                    disk_choices.append(display_name)
                    disk_info[disk_path] = {
                        'size': disk_size,
                        'model': disk_model,
                        'type': disk_type
                    }

            def on_select():
                selection = disk_listbox.curselection()
                if selection:
                    selected_display = disk_listbox.get(selection[0])
                    selected_path = selected_display.split()[0]
                    if on_done:
                        on_done(selected_path, disk_info[selected_path])

            self.clear_ui()
            tk.Label(
                self.main_frame,
                text=prompt,
                bg='#1E1E1E',
                fg='#FFFFFF',
                font=self.disk_selection_font
            ).pack(pady=10)

            listbox_frame = tk.Frame(self.main_frame, bg='#1E1E1E')
            listbox_frame.pack(fill='both', expand=True, padx=10, pady=10)
            scrollbar = tk.Scrollbar(listbox_frame, orient="vertical", bg='#1E1E1E')
            scrollbar.pack(side='right', fill='y')

            disk_listbox = tk.Listbox(
                listbox_frame,
                selectmode=tk.SINGLE,
                bg='#2C3E50',
                fg='#FFFFFF',
                font=self.disk_selection_font,
                yscrollcommand=scrollbar.set
            )
            disk_listbox.pack(fill='both', expand=True)
            scrollbar.config(command=disk_listbox.yview)

            for disk in disk_choices:
                disk_listbox.insert(tk.END, disk)

            if preselect:
                try:
                    index = disk_choices.index(f"{preselect} (SIZE)")
                    disk_listbox.select_set(index)
                    disk_listbox.see(index)
                except ValueError:
                    pass

            tk.Button(
                self.main_frame,
                text="OK",
                command=on_select,
                font=self.font,
                bg='#a5de37',
                fg='#000000',
                relief='flat'
            ).pack(pady=10)

            self.add_back_button()

        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to list disks: {e}")

    def file_to_disk(self):
        self.selected_file = self.choose_file("Select file to flash to disk")
        if not self.selected_file:
            self.initialize_ui()
            return
        self.total_size = os.path.getsize(self.selected_file)
        self.choose_disk("Choose disk to write to:", on_done=self.set_destination_disk)

    def disk_to_disk(self):
        self.choose_disk("Choose disk to read from (source):", on_done=self.set_source_disk)

    def set_source_disk(self, disk_path, disk_info):
        self.selected_source_disk = disk_path
        self.disk_info[disk_path] = disk_info
        try:
            self.total_size = int(subprocess.check_output(
                ["sudo", "blockdev", "--getsize64", disk_path]
            ).strip())
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to get size of source disk: {e}")
            self.initialize_ui()
            return
        self.choose_disk("Choose disk to write to (destination):", on_done=self.set_destination_disk)

    def set_destination_disk(self, disk_path, disk_info):
        self.selected_destination_disk = disk_path
        self.disk_info[disk_path] = disk_info
        self.show_confirmation()

    def show_confirmation(self):
        self.clear_ui()
        if self.selected_file:  # File to Disk
            confirmation_message = (
                f"You are about to flash:\n{os.path.basename(self.selected_file)}\n"
                f"to:\n{self.selected_destination_disk}"
            )
        else:  # Disk to Disk
            confirmation_message = (
                f"You are about to clone:\n{self.selected_source_disk}\n"
                f"to:\n{self.selected_destination_disk}"
            )

        tk.Label(
            self.main_frame,
            text=confirmation_message,
            bg='#1E1E1E',
            fg='#FFFFFF',
            font=("Segoe UI", 14, "bold")
        ).pack(pady=20)

        if not self.selected_file:  # Only show warning for disk operations
            warning_label = tk.Label(
                self.main_frame,
                text="WARNING: This will destroy all data on the destination disk!",
                bg='#1E1E1E',
                fg='#FF4D00',
                font=("Segoe UI", 12, "bold")
            )
            warning_label.pack(pady=10)

        button_frame = tk.Frame(self.main_frame, bg='#1E1E1E')
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="Cancel",
            command=self.initialize_ui,
            font=self.font,
            bg='#FF4D00',
            fg='#FFFFFF',
            relief='flat'
        ).pack(side='left', padx=10)

        tk.Button(
            button_frame,
            text="Continue",
            command=self.show_progress,
            font=self.font,
            bg='#a5de37',
            fg='#000000',
            relief='flat'
        ).pack(side='right', padx=10)

    def show_progress(self):
        self.clear_ui()
        if self.selected_file:
            self.task_message = f"Flashing {os.path.basename(self.selected_file)} to {self.selected_destination_disk}"
        else:
            self.task_message = f"Cloning {self.selected_source_disk} to {self.selected_destination_disk}"

        tk.Label(
            self.main_frame,
            text=self.task_message,
            bg='#1E1E1E',
            fg='#FFFFFF',
            font=("Segoe UI", 14, "bold")
        ).pack(pady=10)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            'custom.Horizontal.TProgressbar',
            troughcolor='#1E1E1E',
            background='#a5de37',
            thickness=10
        )

        self.progress_bar = ttk.Progressbar(
            self.main_frame,
            length=500,
            mode='determinate',
            style='custom.Horizontal.TProgressbar'
        )
        self.progress_bar.pack(pady=10, fill='x')

        self.progress_info = tk.Label(
            self.main_frame,
            text="Copied: 0 MB, 0% Done",
            bg='#1E1E1E',
            fg='#FFFFFF',
            font=("Segoe UI", 12)
        )
        self.progress_info.pack(pady=10)

        button_frame = tk.Frame(self.main_frame, bg='#1E1E1E')
        button_frame.pack(pady=10)

        self.cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_dd,
            font=self.font,
            bg='#FF4D00',
            fg='#FFFFFF',
            relief='flat'
        )
        self.cancel_button.pack(fill='x', padx=10)

        threading.Thread(target=self.execute_dd).start()

    def update_progress(self, line):
        match = re.search(r'(\d+) bytes', line)
        if match:
            copied_bytes = int(match.group(1))
            copied_mb = copied_bytes / (1024 * 1024)
            if self.total_size > 0:
                progress_percentage = min((copied_bytes / self.total_size) * 100, 100)
                copied_mb_formatted = f"{int(copied_mb):04d}"
                self.root.after(0, self.progress_bar.config, {'value': progress_percentage})
                self.root.after(0, self.progress_info.config, {
                    'text': f"Copied: {copied_mb_formatted} MB, {progress_percentage:.0f}% Done"
                })

    def execute_dd(self):
        if self.selected_file and self.selected_destination_disk:
            src = self.selected_file
            dest = self.selected_destination_disk
        elif self.selected_source_disk and self.selected_destination_disk:
            src = self.selected_source_disk
            dest = self.selected_destination_disk
        else:
            return

        try:
            self.process = subprocess.Popen(
                ["sudo", "dd", f"if={src}", f"of={dest}", "bs=4M", "conv=fdatasync", "status=progress"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            while True:
                if self.cancelled:
                    break
                    
                line = self.process.stderr.readline()
                if not line:
                    break
                self.root.after(0, self.update_progress, line.strip())
            
            self.process.wait()
            if self.cancelled:
                self.root.after(0, self.show_operation_result, 
                              "Operation cancelled", 
                              False)
            elif self.process.returncode == 0:
                self.root.after(0, self.show_operation_result, 
                              "Operation completed successfully", 
                              True)
            else:
                raise subprocess.CalledProcessError(self.process.returncode, self.process.args)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode().strip() if e.stderr else str(e)
            self.root.after(0, self.show_operation_result, 
                          f"Operation failed: {error_msg}", 
                          False)
        finally:
            self.process = None

    def cancel_dd(self):
        if hasattr(self, 'process') and self.process:
            self.process.send_signal(signal.SIGINT)
            self.process = None
        self.cancelled = True
        self.initialize_ui()

    def create_partition_table(self):
        def on_disk_selected(disk_path, disk_info):
            self.selected_source_disk = disk_path
            self.disk_info[disk_path] = disk_info
            self.show_partition_table_options()

        self.choose_disk("Select disk to create partition table:", on_done=on_disk_selected)

    def show_partition_table_options(self):
        self.clear_ui()
        tk.Label(
            self.main_frame,
            text=f"Select partition table type for {self.selected_source_disk}",
            bg='#1E1E1E',
            fg='#FFFFFF',
            font=("Segoe UI", 14, "bold")
        ).pack(pady=20)

        button_frame = tk.Frame(self.main_frame, bg='#1E1E1E')
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="MBR (msdos)",
            command=lambda: self.confirm_partition_table("msdos"),
            font=self.font,
            bg='#a5de37',
            fg='#000000',
            relief='flat',
            width=15
        ).pack(side='left', padx=10)

        tk.Button(
            button_frame,
            text="GPT",
            command=lambda: self.confirm_partition_table("gpt"),
            font=self.font,
            bg='#a5de37',
            fg='#000000',
            relief='flat',
            width=15
        ).pack(side='left', padx=10)

        self.add_back_button()

    def confirm_partition_table(self, table_type):
        self.clear_ui()
        tk.Label(
            self.main_frame,
            text=f"You are about to create a {table_type} partition table on:\n{self.selected_source_disk}",
            bg='#1E1E1E',
            fg='#FFFFFF',
            font=("Segoe UI", 14, "bold")
        ).pack(pady=20)

        warning_label = tk.Label(
            self.main_frame,
            text="WARNING: This will destroy all data on this disk!",
            bg='#1E1E1E',
            fg='#FF4D00',
            font=("Segoe UI", 12, "bold")
        )
        warning_label.pack(pady=10)

        button_frame = tk.Frame(self.main_frame, bg='#1E1E1E')
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="Cancel",
            command=self.initialize_ui,
            font=self.font,
            bg='#FF4D00',
            fg='#FFFFFF',
            relief='flat'
        ).pack(side='left', padx=10)

        tk.Button(
            button_frame,
            text="Continue",
            command=lambda: self.create_actual_partition_table(table_type),
            font=self.font,
            bg='#a5de37',
            fg='#000000',
            relief='flat'
        ).pack(side='right', padx=10)

    def create_actual_partition_table(self, table_type):
        self.clear_ui()
        tk.Label(
            self.main_frame,
            text=f"Creating {table_type} partition table on {self.selected_source_disk}...",
            bg='#1E1E1E',
            fg='#FFFFFF',
            font=("Segoe UI", 14, "bold")
        ).pack(pady=20)

        self.progress_info = tk.Label(
            self.main_frame,
            text="Working...",
            bg='#1E1E1E',
            fg='#FFFFFF',
            font=("Segoe UI", 12)
        )
        self.progress_info.pack(pady=10)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            'custom.Horizontal.TProgressbar',
            troughcolor='#1E1E1E',
            background='#a5de37',
            thickness=10
        )

        self.progress_bar = ttk.Progressbar(
            self.main_frame,
            length=500,
            mode='indeterminate',
            style='custom.Horizontal.TProgressbar'
        )
        self.progress_bar.pack(pady=10, fill='x')
        self.progress_bar.start()

        threading.Thread(target=lambda: self.run_create_partition_table(table_type)).start()

    def run_create_partition_table(self, table_type):
        try:
            result = subprocess.run(
                ["sudo", "parted", "-s", self.selected_source_disk, "mklabel", table_type],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.root.after(0, self.show_operation_result, 
                          f"Successfully created {table_type} partition table on {self.selected_source_disk}", 
                          True)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode().strip() if e.stderr else str(e)
            self.root.after(0, self.show_operation_result, 
                          f"Failed to create partition table: {error_msg}", 
                          False)

    def format_disk(self):
        def on_disk_selected(disk_path, disk_info):
            self.selected_source_disk = disk_path
            self.disk_info[disk_path] = disk_info
            self.show_filesystem_options()

        self.choose_disk("Select disk/partition to format:", on_done=on_disk_selected)

    def show_filesystem_options(self):
        self.clear_ui()
        tk.Label(
            self.main_frame,
            text=f"Select filesystem for {self.selected_source_disk}",
            bg='#1E1E1E',
            fg='#FFFFFF',
            font=("Segoe UI", 14, "bold")
        ).pack(pady=20)

        filesystems = [
            ("FAT16", "fat16"), ("FAT32", "fat32"), ("exFAT", "exfat"),
            ("NTFS", "ntfs"), ("BTRFS", "btrfs"), ("EXT2", "ext2"),
            ("EXT3", "ext3"), ("EXT4", "ext4"), ("LUKS", "luks")
        ]

        button_frame = tk.Frame(self.main_frame, bg='#1E1E1E')
        button_frame.pack(pady=10)

        for i, (label, fs_type) in enumerate(filesystems):
            row = i // 3
            col = i % 3
            tk.Button(
                button_frame,
                text=label,
                command=partial(self.confirm_format_disk, fs_type),
                font=self.font,
                bg='#a5de37',
                fg='#000000',
                relief='flat',
                width=10
            ).grid(row=row, column=col, padx=5, pady=5)

        self.add_back_button()

    def confirm_format_disk(self, fs_type):
        self.clear_ui()
        tk.Label(
            self.main_frame,
            text=f"You are about to format:\n{self.selected_source_disk}\nas {fs_type.upper()}",
            bg='#1E1E1E',
            fg='#FFFFFF',
            font=("Segoe UI", 14, "bold")
        ).pack(pady=20)

        warning_label = tk.Label(
            self.main_frame,
            text="WARNING: This will destroy all data on this disk/partition!",
            bg='#1E1E1E',
            fg='#FF4D00',
            font=("Segoe UI", 12, "bold")
        )
        warning_label.pack(pady=10)

        button_frame = tk.Frame(self.main_frame, bg='#1E1E1E')
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="Cancel",
            command=self.initialize_ui,
            font=self.font,
            bg='#FF4D00',
            fg='#FFFFFF',
            relief='flat'
        ).pack(side='left', padx=10)

        tk.Button(
            button_frame,
            text="Format",
            command=lambda: self.format_with_filesystem(fs_type),
            font=self.font,
            bg='#a5de37',
            fg='#000000',
            relief='flat'
        ).pack(side='right', padx=10)

    def format_with_filesystem(self, fs_type):
        self.clear_ui()
        tk.Label(
            self.main_frame,
            text=f"Formatting {self.selected_source_disk} as {fs_type}...",
            bg='#1E1E1E',
            fg='#FFFFFF',
            font=("Segoe UI", 14, "bold")
        ).pack(pady=20)

        self.progress_info = tk.Label(
            self.main_frame,
            text="Working...",
            bg='#1E1E1E',
            fg='#FFFFFF',
            font=("Segoe UI", 12)
        )
        self.progress_info.pack(pady=10)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            'custom.Horizontal.TProgressbar',
            troughcolor='#1E1E1E',
            background='#a5de37',
            thickness=10
        )

        self.progress_bar = ttk.Progressbar(
            self.main_frame,
            length=500,
            mode='indeterminate',
            style='custom.Horizontal.TProgressbar'
        )
        self.progress_bar.pack(pady=10, fill='x')
        self.progress_bar.start()

        threading.Thread(target=lambda: self.run_format_disk(fs_type)).start()

    def run_format_disk(self, fs_type):
        try:
            if fs_type == "luks":
                process = subprocess.Popen(
                    ["sudo", "cryptsetup", "luksFormat", self.selected_source_disk],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                process.communicate(input="YES\n")
                if process.returncode != 0:
                    raise subprocess.CalledProcessError(process.returncode, process.args)
            else:
                if fs_type.startswith("fat"):
                    cmd = ["sudo", "mkfs.vfat", "-F", fs_type[3:], self.selected_source_disk]
                elif fs_type == "exfat":
                    cmd = ["sudo", "mkfs.exfat", self.selected_source_disk]
                elif fs_type == "ntfs":
                    cmd = ["sudo", "mkfs.ntfs", "-Q", self.selected_source_disk]
                elif fs_type.startswith("ext"):
                    cmd = ["sudo", f"mkfs.{fs_type}", self.selected_source_disk]
                elif fs_type == "btrfs":
                    cmd = ["sudo", "mkfs.btrfs", "-f", self.selected_source_disk]
                
                result = subprocess.run(
                    cmd,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

            self.root.after(0, self.show_operation_result, 
                          f"Successfully formatted {self.selected_source_disk} as {fs_type}", 
                          True)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode().strip() if e.stderr else str(e)
            self.root.after(0, self.show_operation_result, 
                          f"Failed to format disk: {error_msg}", 
                          False)

    def secure_erase(self):
        def on_disk_selected(disk_path, disk_info):
            self.selected_source_disk = disk_path
            self.disk_info[disk_path] = disk_info
            self.show_erase_options()

        self.choose_disk("Select disk to securely erase:", on_done=on_disk_selected)

    def show_erase_options(self):
        self.clear_ui()
        tk.Label(
            self.main_frame,
            text=f"Select erase method for {self.selected_source_disk}",
            bg='#1E1E1E',
            fg='#FFFFFF',
            font=("Segoe UI", 14, "bold")
        ).pack(pady=20)

        button_frame = tk.Frame(self.main_frame, bg='#1E1E1E')
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="/dev/zero (1 pass)",
            command=lambda: self.confirm_secure_erase("/dev/zero", 1),
            font=self.font,
            bg='#a5de37',
            fg='#000000',
            relief='flat'
        ).pack(pady=5)

        tk.Button(
            button_frame,
            text="/dev/random (3 passes)",
            command=lambda: self.confirm_secure_erase("/dev/random", 3),
            font=self.font,
            bg='#a5de37',
            fg='#000000',
            relief='flat'
        ).pack(pady=5)

        tk.Button(
            button_frame,
            text="/dev/urandom (7 passes)",
            command=lambda: self.confirm_secure_erase("/dev/urandom", 7),
            font=self.font,
            bg='#a5de37',
            fg='#000000',
            relief='flat'
        ).pack(pady=5)

        self.add_back_button()

    def confirm_secure_erase(self, source, passes):
        self.clear_ui()
        tk.Label(
            self.main_frame,
            text=f"You are about to securely erase:\n{self.selected_source_disk}\nwith {passes} passes of {source}",
            bg='#1E1E1E',
            fg='#FFFFFF',
            font=("Segoe UI", 14, "bold")
        ).pack(pady=20)

        warning_label = tk.Label(
            self.main_frame,
            text="WARNING: This will destroy all data on this disk!",
            bg='#1E1E1E',
            fg='#FF4D00',
            font=("Segoe UI", 12, "bold")
        )
        warning_label.pack(pady=10)

        button_frame = tk.Frame(self.main_frame, bg='#1E1E1E')
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="Cancel",
            command=self.initialize_ui,
            font=self.font,
            bg='#FF4D00',
            fg='#FFFFFF',
            relief='flat'
        ).pack(side='left', padx=10)

        tk.Button(
            button_frame,
            text="Erase",
            command=lambda: self.execute_secure_erase(source, passes),
            font=self.font,
            bg='#a5de37',
            fg='#000000',
            relief='flat'
        ).pack(side='right', padx=10)

    def execute_secure_erase(self, source, passes):
        self.clear_ui()
        tk.Label(
            self.main_frame,
            text=f"Erasing {self.selected_source_disk} with {passes} passes of {source}",
            bg='#1E1E1E',
            fg='#FFFFFF',
            font=("Segoe UI", 14, "bold")
        ).pack(pady=20)

        self.progress_info = tk.Label(
            self.main_frame,
            text="Starting secure erase...",
            bg='#1E1E1E',
            fg='#FFFFFF',
            font=("Segoe UI", 12)
        )
        self.progress_info.pack(pady=10)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            'custom.Horizontal.TProgressbar',
            troughcolor='#1E1E1E',
            background='#a5de37',
            thickness=10
        )

        self.progress_bar = ttk.Progressbar(
            self.main_frame,
            length=500,
            mode='determinate',
            style='custom.Horizontal.TProgressbar'
        )
        self.progress_bar.pack(pady=10, fill='x')

        button_frame = tk.Frame(self.main_frame, bg='#1E1E1E')
        button_frame.pack(pady=10)

        self.cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            command=self.cancel_operation,
            font=self.font,
            bg='#FF4D00',
            fg='#FFFFFF',
            relief='flat'
        )
        self.cancel_button.pack()

        # Get disk size for progress calculation
        try:
            self.total_size = int(subprocess.check_output(
                ["sudo", "blockdev", "--getsize64", self.selected_source_disk]
            ).strip())
        except subprocess.CalledProcessError as e:
            self.root.after(0, messagebox.showerror, 
                          "Error", 
                          f"Failed to get disk size: {e}")
            self.initialize_ui()
            return

        threading.Thread(target=lambda: self.run_erase(source, passes)).start()

    def run_erase(self, source, passes):
        try:
            for i in range(passes):
                if self.cancelled:
                    break
                    
                self.root.after(0, self.progress_info.config, 
                              {'text': f"Pass {i+1} of {passes} with {source}"})
                
                process = subprocess.Popen(
                    ["sudo", "dd", f"if={source}", f"of={self.selected_source_disk}", "bs=1M", "status=progress"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                self.process = process
                
                while True:
                    if self.cancelled:
                        process.terminate()
                        break
                        
                    line = process.stderr.readline()
                    if not line:
                        break
                    
                    # Update progress
                    match = re.search(r'(\d+) bytes', line)
                    if match:
                        copied_bytes = int(match.group(1))
                        progress = (i * 100 + (copied_bytes / self.total_size * 100)) / passes
                        self.root.after(0, self.progress_bar.config, {'value': progress})
                        self.root.after(0, self.progress_info.config, 
                                      {'text': f"Pass {i+1} of {passes}: {line.strip()}"})
                
                process.wait()
                if process.returncode != 0 and not self.cancelled:
                    raise subprocess.CalledProcessError(process.returncode, process.args)

            if self.cancelled:
                self.root.after(0, self.show_operation_result, 
                              "Secure erase cancelled", 
                              False)
            else:
                self.root.after(0, self.show_operation_result, 
                              f"Secure erase completed successfully with {passes} passes", 
                              True)
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode().strip() if e.stderr else str(e)
            self.root.after(0, self.show_operation_result, 
                          f"Secure erase failed: {error_msg}", 
                          False)

    def create_disk_image(self):
        def on_disk_selected(disk_path, disk_info):
            self.selected_source_disk = disk_path
            self.disk_info[disk_path] = disk_info
            self.choose_image_destination()

        self.choose_disk("Select disk to create image from:", on_done=on_disk_selected)

    def choose_image_destination(self):
        # Generate default filename
        disk_model = self.disk_info[self.selected_source_disk]['model'].replace(" ", "_")
        disk_size = self.disk_info[self.selected_source_disk]['size'].replace(" ", "")
        default_name = f"image-of-{disk_model}-{disk_size}.img"
        
        # Let user select directory
        dest_dir = self.choose_directory("Select directory to save disk image")
        if not dest_dir:
            self.initialize_ui()
            return
            
        self.image_path = os.path.join(dest_dir, default_name)
        self.confirm_create_image()

    def confirm_create_image(self):
        self.clear_ui()
        tk.Label(
            self.main_frame,
            text="You are about to create a disk image with these details:",
            bg='#1E1E1E',
            fg='#FFFFFF',
            font=("Segoe UI", 14, "bold")
        ).pack(pady=10)

        info_frame = tk.Frame(self.main_frame, bg='#1E1E1E')
        info_frame.pack(pady=10)

        tk.Label(
            info_frame,
            text=f"Source Disk: {self.selected_source_disk}",
            bg='#1E1E1E',
            fg='#FFFFFF',
            font=("Segoe UI", 12),
            justify=tk.LEFT
        ).pack(anchor='w')

        tk.Label(
            info_frame,
            text=f"Destination: {self.image_path}",
            bg='#1E1E1E',
            fg='#FFFFFF',
            font=("Segoe UI", 12),
            justify=tk.LEFT
        ).pack(anchor='w')

        tk.Label(
            info_frame,
            text=f"Disk Model: {self.disk_info[self.selected_source_disk]['model']}",
            bg='#1E1E1E',
            fg='#FFFFFF',
            font=("Segoe UI", 12),
            justify=tk.LEFT
        ).pack(anchor='w')

        tk.Label(
            info_frame,
            text=f"Disk Size: {self.disk_info[self.selected_source_disk]['size']}",
            bg='#1E1E1E',
            fg='#FFFFFF',
            font=("Segoe UI", 12),
            justify=tk.LEFT
        ).pack(anchor='w')

        button_frame = tk.Frame(self.main_frame, bg='#1E1E1E')
        button_frame.pack(pady=20)

        tk.Button(
            button_frame,
            text="Cancel",
            command=self.initialize_ui,
            font=self.font,
            bg='#FF4D00',
            fg='#FFFFFF',
            relief='flat'
        ).pack(side='left', padx=10)

        tk.Button(
            button_frame,
            text="Create Image",
            command=self.execute_create_image,
            font=self.font,
            bg='#a5de37',
            fg='#000000',
            relief='flat'
        ).pack(side='right', padx=10)

    def execute_create_image(self):
        try:
            self.clear_ui()
            tk.Label(
                self.main_frame,
                text=f"Creating disk image from {self.selected_source_disk}",
                bg='#1E1E1E',
                fg='#FFFFFF',
                font=("Segoe UI", 14, "bold")
            ).pack(pady=20)

            tk.Label(
                self.main_frame,
                text=f"Saving to: {self.image_path}",
                bg='#1E1E1E',
                fg='#FFFFFF',
                font=("Segoe UI", 12)
            ).pack(pady=10)

            self.progress_info = tk.Label(
                self.main_frame,
                text="Starting disk imaging...",
                bg='#1E1E1E',
                fg='#FFFFFF',
                font=("Segoe UI", 12)
            )
            self.progress_info.pack(pady=10)

            style = ttk.Style()
            style.theme_use('clam')
            style.configure(
                'custom.Horizontal.TProgressbar',
                troughcolor='#1E1E1E',
                background='#a5de37',
                thickness=10
            )

            self.progress_bar = ttk.Progressbar(
                self.main_frame,
                length=500,
                mode='determinate',
                style='custom.Horizontal.TProgressbar'
            )
            self.progress_bar.pack(pady=10, fill='x')

            button_frame = tk.Frame(self.main_frame, bg='#1E1E1E')
            button_frame.pack(pady=10)

            self.cancel_button = tk.Button(
                button_frame,
                text="Cancel",
                command=self.cancel_operation,
                font=self.font,
                bg='#FF4D00',
                fg='#FFFFFF',
                relief='flat'
            )
            self.cancel_button.pack()

            # Get disk size for progress calculation
            self.total_size = int(subprocess.check_output(
                ["sudo", "blockdev", "--getsize64", self.selected_source_disk]
            ).strip())

            threading.Thread(target=self.run_create_image).start()

        except subprocess.CalledProcessError as e:
            self.root.after(0, messagebox.showerror, 
                          "Error", 
                          f"Failed to get disk size: {e}")
            self.initialize_ui()
        except Exception as e:
            self.root.after(0, messagebox.showerror, 
                          "Error", 
                          f"Failed to start disk imaging: {e}")
            self.initialize_ui()

    def run_create_image(self):
        try:
            process = subprocess.Popen(
                ["sudo", "dd", f"if={self.selected_source_disk}", f"of={self.image_path}", "bs=4M", "status=progress"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.process = process
            
            while True:
                if self.cancelled:
                    process.terminate()
                    # Remove partially created image
                    if os.path.exists(self.image_path):
                        os.remove(self.image_path)
                    break
                    
                line = process.stderr.readline()
                if not line:
                    break
                
                # Update progress
                match = re.search(r'(\d+) bytes', line)
                if match:
                    copied_bytes = int(match.group(1))
                    progress_percentage = min((copied_bytes / self.total_size) * 100, 100)
                    self.root.after(0, self.progress_bar.config, {'value': progress_percentage})
                    self.root.after(0, self.progress_info.config, 
                                  {'text': f"Creating image: {line.strip()}"})
            
            process.wait()
            if self.cancelled:
                self.root.after(0, self.show_operation_result, 
                              "Disk imaging cancelled", 
                              False)
            elif process.returncode == 0:
                self.root.after(0, self.show_operation_result, 
                              f"Disk image created successfully at:\n{self.image_path}", 
                              True)
            else:
                raise subprocess.CalledProcessError(process.returncode, process.args)
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode().strip() if e.stderr else str(e)
            # Remove failed image file if it exists
            if os.path.exists(self.image_path):
                os.remove(self.image_path)
            self.root.after(0, self.show_operation_result, 
                          f"Disk imaging failed: {error_msg}", 
                          False)

    def show_operation_result(self, message, success):
        self.clear_ui()
        tk.Label(
            self.main_frame,
            text=message,
            bg='#1E1E1E',
            fg='#FFFFFF' if success else '#FF4D00',
            font=("Segoe UI", 14, "bold")
        ).pack(pady=20)

        button_frame = tk.Frame(self.main_frame, bg='#1E1E1E')
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="Back to Main",
            command=self.initialize_ui,
            font=self.font,
            bg='#a5de37',
            fg='#000000',
            relief='flat'
        ).pack()

    def cancel_operation(self):
        if hasattr(self, 'process') and self.process:
            self.process.terminate()
        self.cancelled = True
        self.initialize_ui()

def main():
    root = tk.Tk()
    app = DDUtilityApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()