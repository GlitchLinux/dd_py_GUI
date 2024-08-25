#!/bin/bash

# Define the path for the temporary Python script
PYTHON_SCRIPT_PATH="/tmp/dd_tmp.py"

# Create or overwrite the Python script
cat << 'EOF' > "$PYTHON_SCRIPT_PATH"
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess
import threading
import re
import os
import signal

class DDUtilityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DD Utility")
        self.root.configure(bg='gray20')

        # Create main frame
        self.main_frame = tk.Frame(self.root, bg='gray20')
        self.main_frame.pack(padx=10, pady=10, fill='both', expand=True)

        self.selected_file = None
        self.selected_source_disk = None
        self.selected_destination_disk = None
        self.total_size = 0  # Total size of source
        self.task_message = ""  # Message to display during operation
        self.process = None  # Reference to the dd process

        self.font = ("Sans", 11, "bold")  # Font for most of the UI
        self.disk_selection_font = ("Sans", 13, "bold")  # Larger font for disk selection window

        self.initialize_ui()

    def initialize_ui(self):
        self.clear_ui()

        self.label = tk.Label(self.main_frame, text="Choose DD Task", bg='gray20', fg='white', font=("Sans", 14, "bold"))
        self.label.pack(pady=10)

        self.file_to_disk_button = tk.Button(self.main_frame, text="File to Disk", command=self.file_to_disk, width=25, font=self.font)
        self.file_to_disk_button.pack(pady=10)

        self.disk_to_disk_button = tk.Button(self.main_frame, text="Disk to Disk", command=self.disk_to_disk, width=25, font=self.font)
        self.disk_to_disk_button.pack(pady=10)

        # Do not explicitly set window size to use system default
        self.root.geometry("")

    def clear_ui(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def choose_file(self):
        return filedialog.askopenfilename(title="Select File", filetypes=[("All Files", "*.*")])

    def choose_disk(self, prompt, preselect=None, on_done=None):
        try:
            # Get device names and sizes
            disk_details = subprocess.check_output(["lsblk", "-dpno", "NAME,SIZE"]).decode().strip().split("\n")
            disk_choices = [f"{line.split()[0]} ({line.split()[1]})" for line in disk_details if line.startswith('/dev/sd')]

            def on_select():
                selection = disk_listbox.curselection()
                if selection:
                    selected = disk_listbox.get(selection[0]).split()[0]  # Extract the device name only
                    if on_done:
                        on_done(selected)

            self.clear_ui()
            tk.Label(self.main_frame, text=prompt, bg='gray20', fg='white', font=self.disk_selection_font).pack(pady=10)

            disk_listbox = tk.Listbox(self.main_frame, selectmode=tk.SINGLE, bg='white', font=self.disk_selection_font)
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

            ok_button = tk.Button(self.main_frame, text="OK", command=on_select, font=self.font)
            ok_button.pack(pady=10)

        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to list disks: {e}")

    def file_to_disk(self):
        self.clear_ui()
        self.selected_file = self.choose_file()
        if not self.selected_file:
            self.initialize_ui()
            return

        self.total_size = os.path.getsize(self.selected_file)
        self.choose_disk("Choose disk to write to:", on_done=self.set_destination_disk)

    def disk_to_disk(self):
        self.clear_ui()
        self.choose_disk("Choose disk to read from (source):", on_done=self.set_source_disk)

    def set_source_disk(self, source):
        if source:
            self.selected_source_disk = source
            # Determine total size of source disk
            try:
                self.total_size = int(subprocess.check_output(["sudo", "blockdev", "--getsize64", source]).strip())
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error", f"Failed to get size of source disk: {e}")
                self.initialize_ui()
                return
            self.choose_disk("Choose disk to write to (destination):", on_done=self.set_destination_disk)

    def set_destination_disk(self, destination):
        if destination:
            self.selected_destination_disk = destination
            self.update_task_message()
            self.show_confirmation()

    def show_confirmation(self):
        # Create confirmation message
        confirmation_message = (
            f"Source Disk: {self.selected_source_disk}\n"
            f"Destination Disk: {self.selected_destination_disk}\n"
            "Do you want to proceed with this operation?"
        )
        result = messagebox.askyesno("Confirm Operation", confirmation_message)
        if result:
            self.show_progress()
        else:
            self.initialize_ui()

    def update_task_message(self):
        if self.selected_file:
            self.task_message = f"Flashing {os.path.basename(self.selected_file)} to {self.selected_destination_disk}"
        elif self.selected_source_disk and self.selected_destination_disk:
            self.task_message = f"Cloning {self.selected_source_disk} to {self.selected_destination_disk}"

    def show_progress(self):
        self.clear_ui()

        # Display the current DD task message
        self.task_label = tk.Label(self.main_frame, text=self.task_message, bg='gray20', fg='white', font=("Sans", 14, "bold"))
        self.task_label.pack(pady=10)

        # Progress bar and info
        self.progress_bar = ttk.Progressbar(self.main_frame, length=280, mode='determinate', style='white.Horizontal.TProgressbar')
        self.progress_bar.pack(pady=10, fill='x')  # Fill the width of the container

        self.progress_info = tk.Label(self.main_frame, text="Copied: 0 MB, 0% Done", bg='gray20', fg='white', font=("Sans", 14, "bold"))
        self.progress_info.pack(pady=10)

        # Frame for centering the cancel button
        button_frame = tk.Frame(self.main_frame, bg='gray20')
        button_frame.pack(pady=10)

        # Cancel button with standardized color
        self.cancel_button = tk.Button(button_frame, text="Cancel", command=self.cancel_dd, font=self.font, bg='gray80', fg='black')
        self.cancel_button.pack()

        # Configure the white progress bar style
        style = ttk.Style()
        style.configure('white.Horizontal.TProgressbar', troughcolor='gray20', background='white', thickness=25)

        # Start the dd process in a separate thread
        threading.Thread(target=self.execute_dd).start()

    def update_progress(self, line):
        # Extracting data from dd output
        match = re.search(r'(\d+) bytes', line)
        if match:
            copied_bytes = int(match.group(1))
            copied_mb = copied_bytes / (1024 * 1024)
            if self.total_size > 0:
                progress_percentage = min((copied_bytes / self.total_size) * 100, 100)
                # Format copied MB to an integer with leading zeros
                copied_mb_formatted = f"{int(copied_mb):04d}"
                self.root.after(0, self.progress_bar.config, {'value': progress_percentage})
                self.root.after(0, self.progress_info.config, {'text': f"Copied: {copied_mb_formatted} MB, {progress_percentage:.0f}% Done"})

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
            self.process = subprocess.Popen(["sudo", "dd", f"if={src}", f"of={dest}", "bs=8M", "conv=fdatasync", "status=progress"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            while True:
                line = self.process.stderr.readline()
                if not line:
                    break
                self.root.after(0, self.update_progress, line.strip())
            self.process.wait()
            self.root.after(0, self.show_completion_message)
        except subprocess.CalledProcessError as e:
            self.root.after(0, messagebox.showerror, "Error", f"DD operation failed: {e}")
        finally:
            self.process = None

    def cancel_dd(self):
        if self.process:
            self.process.send_signal(signal.SIGINT)  # Send SIGINT to stop the process
            self.process = None
        self.root.after(0, self.initialize_ui)

    def show_completion_message(self):
        self.clear_ui()
        self.completion_label = tk.Label(self.main_frame, text="DD operation completed successfully.", bg='gray20', fg='white', font=("Sans", 14, "bold"))
        self.completion_label.pack(pady=10)

        # "Exit" and "New DD" buttons
        self.exit_button = tk.Button(self.main_frame, text="Exit", command=self.root.quit, font=self.font)
        self.exit_button.pack(side='left', padx=10, pady=10)

        self.new_dd_button = tk.Button(self.main_frame, text="New DD", command=self.initialize_ui, font=self.font)
        self.new_dd_button.pack(side='left', padx=10, pady=10)

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
