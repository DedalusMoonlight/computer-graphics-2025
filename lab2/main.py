import os
import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageFilter, ImageOps
import shutil
import numpy as np

def shutil_which(cmd):
    try:
        return shutil.which(cmd)
    except Exception:
        return None

def system_file_picker_image(initialdir=None, title="Select image"):
    plat = sys.platform
    if plat.startswith("win"):
        ps = ("Add-Type -AssemblyName System.Windows.Forms;"
              "$ofd = New-Object System.Windows.Forms.OpenFileDialog;"
              "$ofd.Filter = 'Images|*.png;*.jpg;*.jpeg;*.bmp;*.tiff;*.gif';")
        if initialdir:
            safe_dir = initialdir.replace("\\", "\\\\")
            ps += f"$ofd.InitialDirectory = '{safe_dir}';"
        ps += 'if ($ofd.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { Write-Output $ofd.FileName }'
        cmd = ["powershell", "-NoProfile", "-Command", ps]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=60)
            path = res.stdout.strip()
            if path:
                return path
        except Exception:
            pass

    if plat == "darwin":
        osa_cmd = ['osascript', '-e', 'try', f'  set f to (choose file with prompt "{title}")', '  POSIX path of f', 'on error', '  return ""', 'end try']
        try:
            res = subprocess.run(osa_cmd, capture_output=True, text=True, check=False, timeout=60)
            path = res.stdout.strip()
            if path:
                return path
        except Exception:
            pass

    if plat.startswith("linux"):
        zenity = shutil_which("zenity")
        if zenity:
            cmd = [zenity, "--file-selection", "--title", title, "--file-filter=Images | *.png *.jpg *.jpeg *.bmp *.tiff *.gif"]
            if initialdir:
                cmd += ["--filename", os.path.join(initialdir, "")]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=60)
                path = res.stdout.strip()
                if path:
                    return path
            except Exception:
                pass
        kdialog = shutil_which("kdialog")
        if kdialog:
            cmd = [kdialog, "--getopenfilename"]
            if initialdir:
                cmd.append(initialdir)
            cmd.append("*.png *.jpg *.jpeg *.bmp *.tiff *.gif")
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=60)
                path = res.stdout.strip()
                if path:
                    return path
            except Exception:
                pass

    return None

def otsu_threshold(grayscale_image):
    arr = np.array(grayscale_image).ravel()
    hist, _ = np.histogram(arr, bins=256, range=(0, 256))
    total = arr.size
    sum_total = (np.arange(256) * hist).sum()
    weight_bg = 0.0
    sum_bg = 0.0
    var_max = 0.0
    thresh = 0
    for i in range(256):
        weight_bg += hist[i]
        if weight_bg == 0:
            continue
        weight_fg = total - weight_bg
        if weight_fg == 0:
            break
        sum_bg += i * hist[i]
        mean_bg = sum_bg / weight_bg
        mean_fg = (sum_total - sum_bg) / weight_fg
        var_between = weight_bg * weight_fg * (mean_bg - mean_fg) ** 2
        if var_between > var_max:
            var_max = var_between
            thresh = i
    return int(thresh)

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Filters")
        self.root.geometry("1400x900")
        self.original = None
        self.processed = None
        self.photo_original = None
        self.photo_processed = None
        pictures = os.path.expanduser("~/Pictures")
        self.last_dir = pictures if os.path.isdir(pictures) else os.path.expanduser("~")
        self._build_ui()

    def _build_ui(self):
        left = tk.Frame(self.root, padx=8, pady=8)
        left.pack(side=tk.LEFT, fill=tk.Y)
        tk.Button(left, text="Open", width=14, command=self.open_native).pack(pady=6)
        tk.Label(left, text="Size").pack()
        self.size_var = tk.IntVar(value=3)
        self.size_scale = tk.Scale(left, from_=3, to=21, orient='horizontal', resolution=2, variable=self.size_var, length=140)
        self.size_scale.pack(pady=4)
        tk.Label(left, text="Filters").pack(pady=(6,0))
        tk.Button(left, text="Min", width=14, command=lambda: self.apply('min')).pack(pady=4)
        tk.Button(left, text="Median", width=14, command=lambda: self.apply('median')).pack(pady=4)
        tk.Button(left, text="Max", width=14, command=lambda: self.apply('max')).pack(pady=4)
        tk.Label(left, text="Threshold").pack(pady=(8,0))
        self.thresh_var = tk.IntVar(value=128)
        self.thresh_scale = tk.Scale(left, from_=0, to=255, orient='horizontal', variable=self.thresh_var, length=140, command=self._on_thresh_change)
        self.thresh_scale.pack(pady=4)
        tk.Button(left, text="Otsu", width=14, command=self.threshold_otsu).pack(pady=(6,4))
        tk.Button(left, text="Reset", width=14, command=self.reset).pack(pady=(12,4))
        tk.Button(left, text="Save", width=14, command=self.save).pack(pady=4)
        right = tk.Frame(self.root, padx=6, pady=6)
        right.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        self.canvas_orig = tk.Canvas(right, bg='#111')
        self.canvas_proc = tk.Canvas(right, bg='#111')
        self.canvas_orig.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        self.canvas_proc.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        self.canvas_orig.bind('<Configure>', lambda e: self._redraw())
        self.canvas_proc.bind('<Configure>', lambda e: self._redraw())

    def open_native(self):
        path = system_file_picker_image(initialdir=self.last_dir, title="Select image")
        if not path:
            path = filedialog.askopenfilename(initialdir=self.last_dir, filetypes=[("Images","*.png;*.jpg;*.jpeg;*.bmp;*.tiff;*.gif")], parent=self.root)
        if not path or not os.path.isfile(path):
            return
        try:
            img = Image.open(path).convert('RGB')
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        self.last_dir = os.path.dirname(path)
        self.original = img
        self.processed = img.copy()
        self.thresh_var.set(128)
        self._redraw()

    def apply(self, kind):
        if self.original is None:
            return
        size = int(self.size_var.get())
        if size < 3 or size % 2 == 0:
            messagebox.showerror("Error", "Odd size >=3 required")
            return
        if kind == 'min':
            out = self.original.filter(ImageFilter.MinFilter(size))
        elif kind == 'median':
            out = self.original.filter(ImageFilter.MedianFilter(size))
        elif kind == 'max':
            out = self.original.filter(ImageFilter.MaxFilter(size))
        else:
            return
        self.processed = out
        self._redraw()

    def _on_thresh_change(self, val):
        if self.original is None:
            return
        v = int(float(val))
        gray = ImageOps.grayscale(self.original)
        arr = np.array(gray)
        binarized = (arr > v).astype(np.uint8) * 255
        self.processed = Image.fromarray(binarized).convert('RGB')
        self._redraw()

    def threshold_otsu(self):
        if self.original is None:
            return
        gray = ImageOps.grayscale(self.original)
        t = otsu_threshold(gray)
        self.thresh_var.set(t)
        arr = np.array(gray)
        binarized = (arr > t).astype(np.uint8) * 255
        self.processed = Image.fromarray(binarized).convert('RGB')
        self._redraw()

    def reset(self):
        if self.original is None:
            return
        self.processed = self.original.copy()
        self.thresh_var.set(128)
        self._redraw()

    def save(self):
        if self.processed is None:
            return
        path = filedialog.asksaveasfilename(defaultextension='.png', initialdir=self.last_dir, filetypes=[('PNG','*.png'),('JPEG','*.jpg;*.jpeg')], parent=self.root)
        if not path:
            return
        try:
            self.processed.save(path)
            self.last_dir = os.path.dirname(path)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _fit_image_to_canvas(self, pil_img, canvas):
        cw = canvas.winfo_width()
        ch = canvas.winfo_height()
        iw, ih = pil_img.size
        scale_w = cw / iw
        scale_h = ch / ih
        scale = min(scale_w, scale_h, 1.0)  # никогда не превышаем размер холста
        # Дополнительно: если изображение слишком маленькое, увеличим его минимум в 2 раза, но не больше холста
        if iw * scale < cw * 0.5 or ih * scale < ch * 0.5:
            scale = min(max(scale, 2.0), min(scale_w, scale_h))
        nw = max(1, int(iw * scale))
        nh = max(1, int(ih * scale))
        return pil_img.resize((nw, nh), Image.LANCZOS)


    def _redraw(self):
        self.canvas_orig.delete('all')
        self.canvas_proc.delete('all')

        if self.original:
            disp = self._fit_image_to_canvas(self.original, self.canvas_orig)
            self.photo_original = ImageTk.PhotoImage(disp)
            cw = self.canvas_orig.winfo_width()
            ch = self.canvas_orig.winfo_height()
            self.canvas_orig.create_image(cw//2, ch//2, image=self.photo_original, anchor='center')

        if self.processed:
            disp2 = self._fit_image_to_canvas(self.processed, self.canvas_proc)
            self.photo_processed = ImageTk.PhotoImage(disp2)
            cw = self.canvas_proc.winfo_width()
            ch = self.canvas_proc.winfo_height()
            self.canvas_proc.create_image(cw//2, ch//2, image=self.photo_processed, anchor='center')



def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
