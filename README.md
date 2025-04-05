
# **DD Py GUI**  
### *The Pythonic Disk Manipulation Tool* | Graphical User Interface for `dd` tasks!

---

![Image](https://github.com/user-attachments/assets/e141eb14-290b-4a3f-a292-0e90691ee6ed)

---

## **🔥 Features**  
- **Disk Operations**  
  - 🚀 Disk-to-disk cloning  
  - 📥 Flash ISO/IMG files to disks  
  - 🗄️ Create disk images (auto-named `image-of-[DISK]-[SIZE].img`)  
  - ⚠️ Secure wipe (with /dev/zero, /dev/random)  

- **Partition Magic**  
  - 📊 Create MBR/GPT partition tables  
  - 🧹 Format as FAT32/NTFS/EXT4/BTRFS/LUKS  

- **User Experience**  
  - 🎨 Dark theme interface  
  - 🔍 Disk preview with models/sizes  
  - 📊 Real-time progress with ETA  

---

## **💻 Installation**  
### **Debian/Ubuntu**  
```bash
# Install .deb package (recommended)
wget https://github.com/GlitchLinux/dd_py_GUI/releases/download/dd_gui_amd64_v1.1/dd_gui_amd64_v1.1.deb
sudo dpkg -i dd_gui_amd64_v1.1.deb && rm dd_gui_amd64_v1.1.deb 

# Or manually
git clone https://github.com/GlitchLinux/dd_py_GUI.git
cd dd_py_GUI
sudo apt install python3-tk zenity
python3 DD-GUI.py
```

### **Dependencies**  
```bash
sudo apt install python3-tk zenity coreutils lsblk parted \
  dosfstools ntfs-3g e2fsprogs btrfs-progs cryptsetup
```

![Image](https://github.com/user-attachments/assets/c0ae7282-9d79-4cb2-879d-36a0d0ec8c44)


---

## **📦 File Locations**  
| Path | Purpose |  
|------|---------|  
| `/etc/dd_gui/` | Main app directory |  
| `/usr/share/applications/dd_gui.desktop` | Desktop shortcut |  

---

## **🚨 Safety Notice**  
> ❗ **This tool can ERASE data permanently!**  
> - Always double-check target devices  
> - Requires `sudo` for disk operations  

---

## **🌱 Roadmap**  
- **v1.2**  
  - ✅ Checksum verification (MD5/SHA-1)  
  - ✅ LUKS encryption support  
  - ✅ Preset profiles for common tasks  

---

## **📜 License**  
MIT License - Free for personal and commercial use.  

---

## **💡 Pro Tip**  
```bash
# List disks safely before operations:
sudo lsblk -o NAME,SIZE,MODEL,MOUNTPOINT
```

---

## **First Release (v1.0) Highlights**  
- **Stable core functionality** after 50+ test cycles  
- **Fixed** progress bar in disk imaging  
- **Added** /dev/loop device support  
- **Optimized** GUI for 1080p displays  

---

### **For Developers**  
```python
# Customize the 25% smaller app icon:
icon = PhotoImage(file='/etc/dd_gui/DD_GUI.png').subsample(4,4)
```

---

## **📊 1.0 Release Stats**  
| Metric | Value |  
|--------|-------|  
| Code Lines | 1,200+ |  
| Tested Devices | 15+ |  
| Max Disk Size | 16TB (tested) |  

---

### **📮 Support**  
Found a bug? Open an [issue](https://github.com/GlitchLinux/dd_py_GUI/issues).  
**Star ⭐ the repo if you find it useful!**  

---
https://glitchlinux.wtf | 2025 
---
