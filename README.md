# Project Conveyor 🚀
### Infinite Scrollable Tiling Prototype for Windows

**Project Conveyor** is a Python-based window management prototype that brings the **Scrollable Tiling** concept from the Linux (Wayland) ecosystem to the Windows operating system. The name "Conveyor" represents how application windows are arranged on a linear, infinite horizontal strip, much like a conveyor belt.

## 📺 Demo
![Scrolling Demo 1](scrolling1.gif)
![Scrolling Demo 2](scrolling2.gif)

---

## 💡 Inspiration & Concept
This project is heavily inspired by:
*   **Niri**: A scrollable Wayland compositor that reimagines window management as a sequence of horizontal columns.
*   **PaperWM**: A GNOME extension that popularized the scrollable tiling concept.

The primary goal of **Conveyor** is to provide a more natural, intuitive, and productive window navigation experience for Windows users, especially those who work with multiple applications simultaneously.

---

## ✨ Current Features (Prototype Stage)
*   **Infinite Horizontal Strip**: Application windows are organized side-by-side on an endless horizontal axis.
*   **Smooth Scrolling (Lerp)**: Fluid window movement using Linear Interpolation-based animations.
*   **Natural Input Support**: 
    *   **Keyboard**: Navigation via arrow keys.
    *   **Mouse/Trackpad**: Support for scroll wheel and two-finger swipe gestures (Trackpad) by holding the **`Win + Alt`** modifier.
*   **Dynamic Tiling (Tiling Snapping)**: Instantly change the active window's width using presets:
    *   `Win + Alt + 1` : 25% Screen Width (Sidebar)
    *   `Win + Alt + 2` : 50% Screen Width (Split)
    *   `Win + Alt + 3` : 75% Screen Width (Focus)
    *   `Win + Alt + 4` : 100% Screen Width (Full)
*   **Floating Windows**: Toggle any window to be independent of the tiling strip.
*   **Auto-Snapping**: Windows automatically snap to the center of the screen when scrolling stops.
*   **Smart Detection**: Automatically detects when windows are opened, closed, minimized, or restored from the Taskbar.
*   **Responsive Layout**: Automatically adapts the layout when monitor resolution or orientation changes.

---

## ⚠️ Limitations & Known Issues
As a prototype, **Conveyor** currently has several technical limitations:
1.  **Hot Zones Snapping**: The feature to snap windows by dragging them to screen edges (Aero Snap style) is not yet fully stable in this Python version due to system coordinate restrictions within the Windows Sandbox environment.
2.  **Fullscreen/Maximize Handling**: The script does not yet have specific logic to handle windows in *Fullscreen* or *Maximized* modes. These windows may still be forced into the strip layout.
3.  **Double Scrolling**: When scrolling the strip using a mouse, the application under the cursor may still scroll slightly (to be resolved in a future C++/PowerToys implementation).

---

## 🛠️ How to Run (Testing)
This project is designed to be tested safely within **Windows Sandbox**.

1.  Copy the project folder into Windows Sandbox.
2.  Run **`setup.bat`** to install the required Python libraries (`pywin32`, `pynput`, `screeninfo`).
3.  Use the **`Hyperscroll.wsb`** file if you wish to launch Sandbox with automatic configuration.
4.  Open several applications (e.g., 3-4 instances of Notepad).
5.  Run the command: `python main.py`
6.  **Controls:**
    *   Hold **`Win + Alt`** + Scroll Mouse/Swipe Trackpad to slide the conveyor.
    *   Hold **`Win + Alt`** + 1/2/3/4 to resize the active window.
    *   Press **`Win + Alt + V`** to toggle the active window as **Floating**.
    *   Press `Esc` to exit.

---

> [!IMPORTANT]
> This is strictly a **PROTOTYPE**. This project was developed as a Proof of Concept (PoC) for potential future integration into tools like PowerToys FancyZones.
