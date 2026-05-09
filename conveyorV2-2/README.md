# Project Conveyor V2 (Python Edition) 🚀
### Infinite Scrollable Tiling for Windows

**Conveyor V2** adalah versi stabil dari window manager hyperscrolling berbasis Python. Versi ini telah dikompilasi menjadi satu file `.exe` yang bisa berjalan di latar belakang tanpa jendela terminal.

## ✨ Fitur Utama Installer V2
1.  **Background Mode**: Berjalan tenang di latar belakang (tanpa console).
2.  **System Tray Integration**: Kelola aplikasi melalui ikon di pojok kanan bawah (Tray).
3.  **Enhanced Window Filtering**: Menyaring jendela dialog dan popup agar barisan tetap rapi.
4.  **Live Config Reload**: Perubahan konfigurasi langsung diterapkan.
5.  **Optimized Performance**: Animasi halus dengan beban CPU minimal.

## 🎮 Kontrol (Modifier: Alt)
*   **Alt + Mouse Wheel**: Geser barisan jendela.
*   **Alt + 1/2/3/4**: Ubah lebar jendela aktif (25% - 100%).
*   **Alt + Q**: Refresh tata letak.

---

## 🛠️ Cara Membuat Installer
1.  Buka folder `Installer_V2`.
2.  Jalankan `build_v2.bat`. Script akan menginstal library yang diperlukan (PyInstaller, pystray, Pillow, dll) dan melakukan kompilasi.
3.  Ambil folder `ConveyorV2_Installer` yang berisi aplikasi siap pakai.

---
> [!IMPORTANT]
> Karena berbasis Python yang dikompilasi, beberapa Antivirus mungkin memberikan peringatan "False Positive". Pastikan untuk memberikan izin (*Allow*) agar fitur Keyboard/Mouse Hook bisa berjalan.
