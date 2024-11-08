# DD Utility GUI

A graphical user interface (GUI) tool for using the `dd` command to copy files and disks. It offers the ability to copy a file to a disk or clone one disk to another with progress tracking and error handling.

![dd-1st-gui](https://github.com/user-attachments/assets/26a111fb-8522-46ff-bfd3-e9476d630959)

## Features

- Choose between "File to Disk" and "Disk to Disk" operations.
- Select source and destination disks using a GUI.
- Progress bar and detailed task info during the operation.
- Cancel ongoing operations at any time.
- Easy-to-use interface built with Python and Tkinter.

## Requirements

- Linux operating system with `dd` command installed.
- Python 3.
- Tkinter library (usually included with Python).
- `lsblk` command for disk listing.

![progress](https://github.com/user-attachments/assets/8ac77f99-05ec-4ec5-8a80-ca3335e3eccb)

## Installation

### 1. Clone the Repository

To get started, clone this repository to your local machine:

```bash
git clone https://github.com/GlitchLinux/dd_py_GUI.git
cd dd_py_GUI
bash dd_GUI.sh
