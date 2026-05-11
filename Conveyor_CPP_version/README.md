# Project Conveyor (C++ Port) 🚀

A high-performance, lightweight window manager for Windows that brings "Hyperscrolling" and horizontal tiling to your workflow. This is a C++ port of the original Python implementation, optimized for lower resource usage and smoother animations.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-0078d7.svg)

## ✨ Key Features
- **Hyperscrolling**: Seamlessly scroll through all your open windows in a horizontal strip.
- **Smart Tiling**: Automatically organizes windows side-by-side with adjustable gaps.
- **Fluid Animations**: High-refresh rate animations using Ease-Out Cubic transitions.
- **Zero Configuration**: Works out of the box with smart defaults for common apps.
- **Lightweight**: Written in native C++ using Win32 API for minimal CPU/RAM footprint.

## ⌨️ Shortcuts

| Action | Shortcut |
| :--- | :--- |
| **Hyperscroll** | `Win` + `Alt` + `Mouse Scroll` |
| **Quick Scroll** | `Win` + `Alt` + `Left/Right Arrow` or `N/M` |
| **Swap Window** | `Win` + `Alt` + `,` (Comma) / `.` (Period) |
| **Toggle Floating** | `Win` + `Alt` + `V` |
| **Resize Window** | `Alt` + `1` (25%), `2` (50%), `3` (75%), `4` (100%) |
| **Refresh List** | `Alt` + `Q` |

## 🛠️ How to Build

1.  **Requirement**: You need a C++ compiler installed (MinGW-w64 / g++ is recommended).
2.  Ensure `g++` is in your System `PATH`.
3.  Run the `build.bat` script.
4.  The executable `Conveyor_CPP.exe` will be generated in the root folder.

## 🛡️ Security & Privacy
This application uses **Windows Low-Level Hooks** (`WH_KEYBOARD_LL` and `WH_MOUSE_LL`) to detect shortcuts globally. 
- **No Data Collection**: Project Conveyor does **not** record, log, or transmit any keystrokes or mouse data.
- **Open Source**: You can review the source code in the `src/` and `include/` directories to verify how input is handled.
- **AV Flags**: Some Antivirus programs may flag the use of hooks as "Keylogging behavior". This is a false positive due to how the global shortcut engine works.

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

---
*Created by [rad14-dev]*
