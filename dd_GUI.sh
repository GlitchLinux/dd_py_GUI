#!/bin/bash

# Define the path for the temporary Python script
PYTHON_SCRIPT_PATH="/tmp/dd_tmp.py"

# Create or overwrite the Python script
cat << 'EOF' > "$PYTHON_SCRIPT_PATH"
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk
import subprocess
import threading
import re
import os
import signal
import time

class DDUtilityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DD GUI Utility")
        self.root.configure(bg='gray20')

        self.main_frame = tk.Frame(self.root, bg='gray20')
        self.main_frame.pack(padx=10, pady=10)  # Padding around the main frame

        self.selected_file = None
        self.selected_source_disk = None
        self.selected_destination_disk = None
        self.process = None
        self.total_size = None  # To store the total size for progress calculation

        self.initialize_ui()

    def initialize_ui(self):
        self.clear_ui()

        self.label = tk.Label(self.main_frame, text="Choose DD Task", bg='gray20', fg='white', font=("Arial", 12, "bold"))
        self.label.pack(pady=5)

        self.file_to_disk_button = tk.Button(self.main_frame, text="File to Disk", command=self.file_to_disk, width=20, font=("Arial", 10, "bold"))
        self.file_to_disk_button.pack(pady=5)

        self.disk_to_disk_button = tk.Button(self.main_frame, text="Disk to Disk", command=self.disk_to_disk, width=20, font=("Arial", 10, "bold"))
        self.disk_to_disk_button.pack(pady=5)

        # Update window size based on content
        self.root.update_idletasks()
        min_height = self.main_frame.winfo_reqheight() + 50
        self.root.geometry(f"{self.main_frame.winfo_reqwidth()}x{min_height}")

    def clear_ui(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def choose_file(self):
        # Try to use Thunar if available
        if self.is_program_available("thunar"):
            return self.open_file_with_thunar()
        else:
            # Fallback to default file dialog
            return filedialog.askopenfilename(title="Select File", filetypes=[("All Files", "*.*")])

    def is_program_available(self, prog):
        return subprocess.call(["which", prog], stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

    def open_file_with_thunar(self):
        try:
            # Use Thunar to select a file
            result = subprocess.run(['zenity', '--file-selection', '--title=Select File'], capture_output=True, text=True)
            file_path = result.stdout.strip()
            if os.path.isfile(file_path):
                return file_path
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file manager: {e}")
            return None

        return None

    def choose_disk(self, prompt, preselect=None, on_done=None):
        try:
            # Get device names and sizes including /dev/mmcblk* and /dev/loop*
            disk_details = subprocess.check_output(["lsblk", "-dpno", "NAME,SIZE"]).decode().strip().split("\n")
            disk_choices = [f"{line.split()[0]} ({line.split()[1]})" for line in disk_details if line.startswith('/dev/sd') or line.startswith('/dev/mmcblk') or line.startswith('/dev/loop')]

            def on_select():
                selection = disk_listbox.curselection()
                if selection:
                    selected = disk_listbox.get(selection[0]).split()[0]  # Extract the device name only
                    if on_done:
                        on_done(selected)

            self.clear_ui()
            tk.Label(self.main_frame, text=prompt, bg='gray20', fg='white', font=("Arial", 10, "bold")).pack(pady=5)

            disk_listbox = tk.Listbox(self.main_frame, selectmode=tk.SINGLE, bg='white', font=("Arial", 10))
            disk_listbox.pack(fill='both', expand=True)

            for disk in disk_choices:
                disk_listbox.insert(tk.END, disk)

            if preselect:
                try:
                    index = disk_choices.index(f"{preselect} (SIZE)")
                    disk_listbox.select_set(index)
                    disk_listbox.see(index)
                except ValueError:
                    pass

            ok_button = tk.Button(self.main_frame, text="OK", command=on_select, font=("Arial", 10, "bold"))
            ok_button.pack(pady=5)

            # Update window size based on content
            self.root.update_idletasks()
            min_height = self.main_frame.winfo_reqheight() + 50
            self.root.geometry(f"{self.main_frame.winfo_reqwidth()}x{min_height}")

        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to list disks: {e}")

    def file_to_disk(self):
        self.clear_ui()
        self.selected_file = self.choose_file()
        if not self.selected_file:
            self.initialize_ui()
            return

        self.choose_disk("Choose disk to write to:", on_done=self.set_destination_disk)

    def disk_to_disk(self):
        self.clear_ui()
        self.choose_disk("Choose disk to read from (source):", on_done=self.set_source_disk)

    def set_source_disk(self, source):
        if source:
            self.selected_source_disk = source
            self.choose_disk("Choose disk to write to (destination):", on_done=self.set_destination_disk)

    def set_destination_disk(self, destination):
        if destination:
            self.selected_destination_disk = destination
            self.show_confirmation()

    def show_confirmation(self):
        if self.selected_file:
            confirmation_message = f"File: {self.selected_file}\nDestination: {self.selected_destination_disk}"
        elif self.selected_source_disk and self.selected_destination_disk:
            confirmation_message = f"Source: {self.selected_source_disk}\nDestination: {self.selected_destination_disk}"
        else:
            confirmation_message = "Invalid selection."

        result = messagebox.askyesno("Confirm DD Task", f"Do you want to execute the following task?\n\n{confirmation_message}")

        if result:
            self.show_progress()
            threading.Thread(target=self.execute_dd).start()
        else:
            self.initialize_ui()

    def show_progress(self):
        self.clear_ui()
        self.progress_label = tk.Label(self.main_frame, text="DD Operation Running:", bg='gray20', fg='white', font=("Arial", 12, "bold"))
        self.progress_label.pack(pady=5)

        self.task_label = tk.Label(self.main_frame, text=self.get_task_description(), bg='gray20', fg='white', font=("Arial", 10, "bold"))
        self.task_label.pack(pady=5)

        self.progress_bar = ttk.Progressbar(self.main_frame, length=300, mode='determinate', style='TProgressbar')
        self.progress_bar.pack(pady=5)

        self.progress_label_amount = tk.Label(self.main_frame, text="0 MB Copied - 0.00% Done", bg='gray20', fg='white', font=("Arial", 10, "bold"))
        self.progress_label_amount.pack(pady=5)

        self.cancel_button = tk.Button(self.main_frame, text="Cancel", command=self.cancel_dd, width=15, font=("Arial", 10, "bold"))
        self.cancel_button.pack(pady=10)

        # Define progress bar style with lime green color
        style = ttk.Style()
        style.configure('TProgressbar',
                        thickness=20,
                        troughcolor='gray80',
                        background='lime green')

        # Update window size based on content
        self.root.update_idletasks()
        min_height = self.main_frame.winfo_reqheight() + 50
        self.root.geometry(f"{self.main_frame.winfo_reqwidth()}x{min_height}")

    def get_task_description(self):
        if self.selected_file:
            return f"Flashing {self.selected_file} to {self.selected_destination_disk}"
        elif self.selected_source_disk and self.selected_destination_disk:
            return f"Cloning {self.selected_source_disk} to {self.selected_destination_disk}"
        return "No task description available"

    def update_progress(self, line):
        if 'bytes' in line:
            try:
                # Extract bytes transferred from `dd` progress output
                match = re.search(r'(\d+) bytes', line)
                if match:
                    bytes_transferred = int(match.group(1))
                    if self.total_size:
                        progress_percentage = min(max(bytes_transferred / self.total_size * 100, 0.00), 100.00)
                    else:
                        progress_percentage = 0.00  # Placeholder if total_size is not set

                    # Convert bytes to MB
                    bytes_transferred_mb = bytes_transferred / 1024**2
                    # Update labels
                    self.root.after(0, self.progress_bar.config, {'value': progress_percentage})
                    self.root.after(0, self.progress_label_amount.config, {'text': f"{bytes_transferred_mb:.2f} MB Copied - {progress_percentage:.2f}% Done"})
            except ValueError:
                pass

    def execute_dd(self):
        if self.selected_file and self.selected_destination_disk:
            src = self.selected_file
            dest = self.selected_destination_disk
        elif self.selected_source_disk and self.selected_destination_disk:
            src = self.selected_source_disk
            dest = self.selected_destination_disk
        else:
            messagebox.showerror("Error", "Source or Destination disk not selected.")
            self.initialize_ui()
            return

        try:
            # Use a larger block size and options to potentially speed up the process
            cmd = ["sudo", "dd", f"if={src}", f"of={dest}", "bs=64M", "conv=fdatasync", "oflag=direct", "status=progress"]
            # Optionally use `ionice` to adjust I/O priority
            cmd = ["ionice", "-c2", "-n0"] + cmd
            # Optionally use `nice` to adjust CPU priority
            cmd = ["nice", "-n-10"] + cmd

            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            last_update_time = time.time()
            while True:
                output = self.process.stderr.readline()
                if output:
                    self.update_progress(output.strip())
                    last_update_time = time.time()
                if self.process.poll() is not None:
                    break
            self.root.after(0, messagebox.showinfo, "DD Completed", "DD operation completed successfully.")
        except subprocess.CalledProcessError as e:
            self.root.after(0, messagebox.showerror, "Error", f"DD operation failed: {e}")
        finally:
            self.root.after(0, self.initialize_ui)

    def cancel_dd(self):
        if self.process:
            os.kill(self.process.pid, signal.SIGINT)
            self.process = None
        self.initialize_ui()

def main():
    root = tk.Tk()
    app = DDUtilityApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
EOF

# Make the Python script executable
chmod +x "$PYTHON_SCRIPT_PATH"

# Run the Python script
python3 "$PYTHON_SCRIPT_PATH"
