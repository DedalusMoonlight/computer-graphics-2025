import tkinter as tk
from tkinter import ttk, messagebox
import colorsys
from functools import partial

def clamp(x, a, b):
    return max(a, min(b, x))


def rgb_to_cmyk(r, g, b):
    if r == 0 and g == 0 and b == 0:
        return 0.0, 0.0, 0.0, 100.0
    r_p, g_p, b_p = r/255.0, g/255.0, b/255.0
    k = 1 - max(r_p, g_p, b_p)
    c = (1 - r_p - k) / (1 - k)
    m = (1 - g_p - k) / (1 - k)
    y = (1 - b_p - k) / (1 - k)
    return round(c*100,4), round(m*100,4), round(y*100,4), round(k*100,4)


def cmyk_to_rgb(c, m, y, k):
    c_p = clamp(c,0,100)/100.0
    m_p = clamp(m,0,100)/100.0
    y_p = clamp(y,0,100)/100.0
    k_p = clamp(k,0,100)/100.0
    r = 255*(1 - c_p)*(1 - k_p)
    g = 255*(1 - m_p)*(1 - k_p)
    b = 255*(1 - y_p)*(1 - k_p)
    return int(round(r)), int(round(g)), int(round(b))


def rgb_to_hsv_deg(r, g, b):
    r_p, g_p, b_p = r/255.0, g/255.0, b/255.0
    h, s, v = colorsys.rgb_to_hsv(r_p, g_p, b_p)
    return round(h*360,4), round(s*100,4), round(v*100,4)


def hsv_deg_to_rgb(h, s, v):
    h_p = (h % 360)/360.0
    s_p = clamp(s,0,100)/100.0
    v_p = clamp(v,0,100)/100.0
    r_p, g_p, b_p = colorsys.hsv_to_rgb(h_p, s_p, v_p)
    return int(round(r_p*255)), int(round(g_p*255)), int(round(b_p*255))


def rgb_to_hex(r,g,b):
    return f"#{r:02X}{g:02X}{b:02X}"


def hex_to_rgb(hexstr):
    s = hexstr.lstrip('#')
    if len(s) == 3:
        s = ''.join([ch*2 for ch in s])
    if len(s) != 6:
        raise ValueError('Bad hex')
    return int(s[0:2],16), int(s[2:4],16), int(s[4:6],16)


DEFAULT_PALETTE = [
    '#000000', '#444444', '#888888', '#CCCCCC', '#FFFFFF',
    '#FF0000', '#FF7F00', '#FFFF00', '#00FF00', '#00FFFF', '#0000FF', '#7F00FF', '#FF00FF',
    '#800000', '#808000', '#008000', '#008080', '#000080', '#800080'
]


class ColorApp:
    def __init__(self, root):
        self.root = root
        root.title('CMYK <-> RGB <-> HSV')
        self.updating = False

        self.r, self.g, self.b = 0, 0, 0
        self.c, self.m, self.y, self.k = rgb_to_cmyk(self.r, self.g, self.b)
        self.h, self.s, self.v = rgb_to_hsv_deg(self.r, self.g, self.b)

        self.palette = DEFAULT_PALETTE.copy()

        self.create_widgets()
        self.update_widgets_from_rgb()

    def create_frame_block(self, parent, title):
        fr = ttk.LabelFrame(parent, text=title, padding=(8,8))
        return fr


    def create_widgets(self):
        palette_frame = ttk.LabelFrame(self.root, text='Palette', padding=(6,6))
        palette_frame.pack(fill='x', padx=8, pady=(8,0))
        self.palette_canvas = tk.Frame(palette_frame)
        self.palette_canvas.pack(fill='x')
        self.draw_palette()

        add_row = ttk.Frame(palette_frame)
        add_row.pack(fill='x', pady=4)
        self.new_hex_var = tk.StringVar()
        ttk.Label(add_row, text='Add hex:').pack(side='left')
        hex_entry = ttk.Entry(add_row, textvariable=self.new_hex_var, width=10)
        hex_entry.pack(side='left', padx=4)
        add_btn = ttk.Button(add_row, text='Add to palette', command=self.add_palette_color)
        add_btn.pack(side='left')

        top = ttk.Frame(self.root)
        top.pack(fill='both', expand=True, padx=8, pady=8)

        cmyk_fr = self.create_frame_block(top, 'CMYK (%)')
        rgb_fr = self.create_frame_block(top, 'RGB (0..255)')
        hsv_fr = self.create_frame_block(top, 'HSV (H°/S%/V%)')
        cmyk_fr.grid(row=0, column=0, sticky='nsew', padx=4, pady=4)
        rgb_fr.grid(row=0, column=1, sticky='nsew', padx=4, pady=4)
        hsv_fr.grid(row=0, column=2, sticky='nsew', padx=4, pady=4)
        top.columnconfigure((0,1,2), weight=1)

        self.c_var = tk.DoubleVar(value=self.c)
        self.m_var = tk.DoubleVar(value=self.m)
        self.y_var = tk.DoubleVar(value=self.y)
        self.k_var = tk.DoubleVar(value=self.k)
        self.make_scale_widget(cmyk_fr, 'C', 0, 100, self.c_var, self.on_cmyk_change)
        self.make_scale_widget(cmyk_fr, 'M', 0, 100, self.m_var, self.on_cmyk_change)
        self.make_scale_widget(cmyk_fr, 'Y', 0, 100, self.y_var, self.on_cmyk_change)
        self.make_scale_widget(cmyk_fr, 'K', 0, 100, self.k_var, self.on_cmyk_change)

        self.r_var = tk.IntVar(value=self.r)
        self.g_var = tk.IntVar(value=self.g)
        self.b_var = tk.IntVar(value=self.b)
        self.make_scale_widget(rgb_fr, 'R', 0, 255, self.r_var, self.on_rgb_change)
        self.make_scale_widget(rgb_fr, 'G', 0, 255, self.g_var, self.on_rgb_change)
        self.make_scale_widget(rgb_fr, 'B', 0, 255, self.b_var, self.on_rgb_change)

        self.h_var = tk.DoubleVar(value=self.h)
        self.s_var = tk.DoubleVar(value=self.s)
        self.v_var = tk.DoubleVar(value=self.v)
        self.make_scale_widget(hsv_fr, 'H', 0, 360, self.h_var, self.on_hsv_change)
        self.make_scale_widget(hsv_fr, 'S', 0, 100, self.s_var, self.on_hsv_change)
        self.make_scale_widget(hsv_fr, 'V', 0, 100, self.v_var, self.on_hsv_change)

        self.r_var.trace_add('write', lambda *a: self.on_rgb_change())
        self.g_var.trace_add('write', lambda *a: self.on_rgb_change())
        self.b_var.trace_add('write', lambda *a: self.on_rgb_change())
        self.c_var.trace_add('write', lambda *a: self.on_cmyk_change())
        self.m_var.trace_add('write', lambda *a: self.on_cmyk_change())
        self.y_var.trace_add('write', lambda *a: self.on_cmyk_change())
        self.k_var.trace_add('write', lambda *a: self.on_cmyk_change())
        self.h_var.trace_add('write', lambda *a: self.on_hsv_change())
        self.s_var.trace_add('write', lambda *a: self.on_hsv_change())
        self.v_var.trace_add('write', lambda *a: self.on_hsv_change())

        bottom = ttk.Frame(self.root, padding=(8,0))
        bottom.pack(fill='x')
        self.preview = tk.Canvas(bottom, height=80)
        self.preview.pack(side='left', fill='x', expand=True, padx=4)
        self.hex_var = tk.StringVar(value=rgb_to_hex(self.r,self.g,self.b))
        hex_lbl = ttk.Label(bottom, textvariable=self.hex_var, font=('TkDefaultFont', 12, 'bold'))
        hex_lbl.pack(side='right', padx=8)


    def draw_palette(self):
        for w in self.palette_canvas.winfo_children():
            w.destroy()

        cols = 12
        pad = 2
        for i, hx in enumerate(self.palette):
            btn = tk.Button(self.palette_canvas, bg=hx, activebackground=hx, width=2, height=1,
                            command=partial(self.pick_hex, hx))
            btn.grid(row=i//cols, column=i%cols, padx=pad, pady=pad)


    def pick_hex(self, hx):
        try:
            r,g,b = hex_to_rgb(hx)
        except Exception:
            return

        self.updating = True
        try:
            self.r, self.g, self.b = r,g,b
            self.c, self.m, self.y, self.k = rgb_to_cmyk(r,g,b)
            self.h, self.s, self.v = rgb_to_hsv_deg(r,g,b)
            self.update_widgets_from_rgb()
        finally:
            self.updating = False


    def add_palette_color(self):
        hx = self.new_hex_var.get().strip()
        if not hx:
            return
        if not hx.startswith('#'):
            hx = '#' + hx
        try:
            _ = hex_to_rgb(hx)
        except Exception:
            messagebox.showerror('Bad hex', 'Please enter a valid hex color like #1A2B3C')
            return

        if hx.upper() not in [p.upper() for p in self.palette]:
            self.palette.insert(0, hx)
            if len(self.palette) > 60:
                self.palette = self.palette[:60]
            self.draw_palette()
            self.new_hex_var.set('')


    def make_scale_widget(self, parent, name, frm, to, var, command):
        row = ttk.Frame(parent)
        row.pack(fill='x', pady=2)
        lbl = ttk.Label(row, text=name, width=3)
        lbl.pack(side='left')
        scale = ttk.Scale(row, from_=frm, to=to, variable=var,
                          command=lambda v, cmd=command: cmd())
        scale.pack(side='left', fill='x', expand=True, padx=4)
        entry = ttk.Entry(row, textvariable=var, width=6)
        entry.pack(side='right')


    def on_rgb_change(self):
        if self.updating: return
        try:
            self.updating = True
            r = int(self.r_var.get())
            g = int(self.g_var.get())
            b = int(self.b_var.get())
        except Exception:
            self.updating = False
            return
        r = clamp(r,0,255); g = clamp(g,0,255); b = clamp(b,0,255)
        self.r, self.g, self.b = r,g,b

        self.c, self.m, self.y, self.k = rgb_to_cmyk(r,g,b)
        self.h, self.s, self.v = rgb_to_hsv_deg(r,g,b)
        self.update_widgets_from_rgb()
        self.updating = False


    def on_cmyk_change(self):
        if self.updating: return
        try:
            c = float(self.c_var.get())
            m = float(self.m_var.get())
            y = float(self.y_var.get())
            k = float(self.k_var.get())
        except Exception:
            return
        c = clamp(c,0,100); m = clamp(m,0,100); y = clamp(y,0,100); k = clamp(k,0,100)
        self.c, self.m, self.y, self.k = c,m,y,k
        self.updating = True
        r,g,b = cmyk_to_rgb(c,m,y,k)
        self.r, self.g, self.b = r,g,b
        self.h, self.s, self.v = rgb_to_hsv_deg(r,g,b)
        self.update_widgets_from_rgb()
        self.updating = False


    def on_hsv_change(self):
        if self.updating: return
        try:
            h = float(self.h_var.get())
            s = float(self.s_var.get())
            v = float(self.v_var.get())
        except Exception:
            return
        h = h % 360
        s = clamp(s,0,100); v = clamp(v,0,100)
        self.h, self.s, self.v = h,s,v
        self.updating = True
        r,g,b = hsv_deg_to_rgb(h,s,v)
        self.r, self.g, self.b = r,g,b
        self.c, self.m, self.y, self.k = rgb_to_cmyk(r,g,b)
        self.update_widgets_from_rgb()
        self.updating = False


    def update_widgets_from_rgb(self):
        self.r_var.set(self.r); self.g_var.set(self.g); self.b_var.set(self.b)
        self.c_var.set(self.c); self.m_var.set(self.m); self.y_var.set(self.y); self.k_var.set(self.k)
        self.h_var.set(self.h); self.s_var.set(self.s); self.v_var.set(self.v)
        self.hex_var.set(rgb_to_hex(self.r,self.g,self.b))
        self.preview.delete('all')
        self.preview.create_rectangle(0,0,1000,80, fill=rgb_to_hex(self.r,self.g,self.b), outline='')


if __name__ == '__main__':
    root = tk.Tk()
    app = ColorApp(root)
    root.mainloop()
