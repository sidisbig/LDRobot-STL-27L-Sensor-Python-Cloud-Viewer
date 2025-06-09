# 🔭 STL-27L LiDAR Live Plotter

This project provides a Python script that reads and visualizes real-time LiDAR scan data from an STL-27L (or compatible) sensor over a serial port. It plots the data in a live, interactive polar plot using Matplotlib.

---

## 📸 Preview


![Screenshot 2025-06-09 163600](https://github.com/user-attachments/assets/f58325eb-e707-4d75-b33e-c83bf339735e)

---

## 🛠 Features

- 🔄 Real-time 360° full-scan plotting
- 🧭 High-resolution (0.167° per bin, 2160 bins)
- 📡 Serial communication with the LiDAR sensor
- 🧹 Clears and redraws scan data after each full revolution
- 🖱️ Mouse wheel support for zooming in/out

---

## 📦 Requirements

Install dependencies via:

```bash
pip install -r requirements.txt
