# DD GUI Utility

A graphical interface for disk management operations using dd and other Linux tools.

                                        ![Image](https://github.com/user-attachments/assets/c0ae7282-9d79-4cb2-879d-36a0d0ec8c44)

## Features

- File to Disk flashing
- Disk to Disk cloning
- Partition table creation (MBR/GPT)
- Disk/partition formatting (FAT, NTFS, EXT, etc.)
- Secure disk erasure
- Disk image creation
- Progress tracking for all operations

## Installation

### From .deb package

1. Download the `dd_gui_amd64_v1.1.deb` package
2. Install with: `sudo dpkg -i dd_gui_amd64_v1.1.deb`
3. Resolve dependencies: `sudo apt-get install -f`

### Dependencies

- Python 3
- tkinter
- zenity
- dd
- lsblk
- parted
- mkfs utilities
- cryptsetup (for LUKS)

Install dependencies on Debian/Ubuntu with:
```bash
sudo apt install python3-tk zenity coreutils util-linux parted dosfstools ntfs-3g btrfs-progs e2fsprogs cryptsetup
