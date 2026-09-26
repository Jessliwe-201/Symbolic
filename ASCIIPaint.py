import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageOps
import tkinter.font as tkfont

# ---------- ПАЛИТРА (тёмная тема) ----------
BG_DARK      = "#1b1b1b"
BG_PANEL     = "#161616"
BG_CANVAS    = "#030303"
FG_TEXT      = "#fcfaff"
FG_MUTED     = "#f7f2f7"
ACCENT       = "#4c0475"
ACCENT_HOVER = "#74a8f7"
DISCORD      = "#23108B"
DISCORD_HOV  = "#4752c4"
BTN_BG       = "#313244"
BTN_HOVER    = "#45475a"
SUCCESS      = "#a6e3a1"
WARNING      = "#f9e2af"
DANGER       = "#f38ba8"
GRID_COLOR   = "#252535"

# Наборы символов от "тёмного" к "светлому"
CHAR_SETS = {
    "Классика":       "@%#*+=-:. ",
    "Блоки █▓▒░":     "█▓▒░ ",
    "Блоки+":         "█▓▒░· ",
    "Плотный":        "@$B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. ",
    "Матрица":        "01 ",
    "Точки":          "●•·. ",
    "Звёзды":         "✦✧✶✷✸·. ",
    "Смайлы":         "😈😎🙂😐😕😟😢😭  ",
    "Стрелки":        "▼▲►◄·. ",
    "Сердца":         "❤💖💗💓💕·. ",
}

# Активный набор (можно менять через выпадающий список)
CHARS = CHAR_SETS["Блоки █▓▒░"]

BRAILLE_MAP = [
    (0, 0, 0x01), (1, 0, 0x08),  # верхние точки
    (0, 1, 0x02), (1, 1, 0x10),
    (0, 2, 0x04), (1, 2, 0x20),
    (0, 3, 0x40), (1, 3, 0x80),  # нижние точки
]


class RoundedButton(tk.Canvas):
    """Кнопка со скруглёнными углами на Canvas."""

    def __init__(self, parent, text, command,
                 bg="#313244", hover="#45475a", fg="#fcfaff",
                 radius=14, padx=18, pady=7,
                 font=("Segoe UI", 10), **kwargs):
        tmp = tkfont.Font(font=font)
        text_w = tmp.measure(text)
        text_h = tmp.metrics("linespace")

        w = text_w + padx * 2
        h = text_h + pady * 2

        super().__init__(parent, width=w, height=h,
                         bg=parent["bg"], highlightthickness=0,
                         bd=0, **kwargs)

        self.command = command
        self.bg_color = bg
        self.hover_color = hover
        self.fg_color = fg
        self.radius = radius
        self.text = text
        self.font = font
        self._current_bg = bg

        self._draw()
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _rounded_rect(self, x1, y1, x2, y2, r, **kw):
        points = [
            x1 + r, y1,
            x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2,
            x1 + r, y2, x1, y2, x1, y2 - r,
            x1, y1 + r, x1, y1, x1 + r, y1,
        ]
        return self.create_polygon(points, smooth=True, **kw)

    def _draw(self):
        self.delete("all")
        w = int(self["width"])
        h = int(self["height"])
        self._rounded_rect(0, 0, w, h, self.radius,
                           fill=self._current_bg, outline="")
        self.create_text(w // 2, h // 2, text=self.text,
                         fill=self.fg_color, font=self.font)

    def _on_enter(self, e):
        self._current_bg = self.hover_color
        self._draw()

    def _on_leave(self, e):
        self._current_bg = self.bg_color
        self._draw()

    def _on_click(self, e):
        self.command()


class AsciiPaint:
    def __init__(self, root):
        self.root = root
        self.root.title("ASCII Paint")
        self.root.geometry("1280x850")
        self.root.minsize(1000, 700)
        self.root.configure(bg=BG_DARK)

        # Исходные размеры холста (для кнопки «Очистить»)
        self.DEFAULT_COLS = 95
        self.DEFAULT_ROWS = 45

        # Текущие размеры
        self.cols = self.DEFAULT_COLS
        self.rows = self.DEFAULT_ROWS

        self.cell_w = 10
        self.cell_h = 16
        self.current_char = "-"
        self.brush_size = 1

        self._build_ui()
        self._new_canvas()

    # ============ ИНТЕРФЕЙС ============
    def _build_ui(self):
        # ----- Заголовок -----
        header = tk.Frame(self.root, bg=BG_DARK)
        header.pack(fill="x", padx=12, pady=(10, 5))

        tk.Label(
            header, text="🎨Symbolic          Made By Jessliwe",
            font=("Segoe UI", 16, "bold"),
            bg=BG_DARK, fg=ACCENT,
        ).pack(side="left")

        # ----- Панель инструментов -----
        panel = tk.Frame(self.root, bg=BG_PANEL)
        panel.pack(fill="x", padx=12, pady=5, ipady=8)

        # Символ
        tk.Label(panel, text="Символ:", font=("Segoe UI", 10),
                 bg=BG_PANEL, fg=FG_TEXT).pack(side="left", padx=(10, 4))
        self.char_entry = tk.Entry(
            panel, width=3, font=("Consolas", 12),
            bg=BTN_BG, fg=FG_TEXT, insertbackground=ACCENT,
            relief="flat", justify="center",
        )
        self.char_entry.insert(0, "-")
        self.char_entry.pack(side="left", ipady=3)
        self.char_entry.bind("<KeyRelease>", self._update_char)

        # Кисть
        tk.Label(panel, text="Кисть:", font=("Segoe UI", 10),
                 bg=BG_PANEL, fg=FG_TEXT).pack(side="left", padx=(15, 4))
        self.brush_size_var = tk.IntVar(value=1)
        spin = tk.Spinbox(
            panel, from_=1, to=10, width=3,
            textvariable=self.brush_size_var,
            font=("Consolas", 11),
            bg=BTN_BG, fg=FG_TEXT, buttonbackground=BTN_BG,
            relief="flat", justify="center",
            command=self._update_brush,
        )
        spin.pack(side="left", ipady=3)

        # Набор символов
        tk.Label(panel, text="Набор:", font=("Segoe UI", 10),
                bg=BG_PANEL, fg=FG_TEXT).pack(side="left", padx=(15, 4))

        self.char_set_var = tk.StringVar(value="Блоки █▓▒░")
        char_set_menu = tk.OptionMenu(panel, self.char_set_var, *CHAR_SETS.keys())
        char_set_menu.config(
            font=("Segoe UI", 9),
            bg=BTN_BG, fg=FG_TEXT,
            activebackground=BTN_HOVER, activeforeground=FG_TEXT,
            relief="flat", bd=0, highlightthickness=0,
            width=12,
        )
        char_set_menu["menu"].config(
            bg=BTN_BG, fg=FG_TEXT,
            activebackground=ACCENT, activeforeground="white",
            font=("Segoe UI", 10),
        )
        char_set_menu.pack(side="left", padx=2)

        self.char_set_var.trace("w", self._on_char_set_change)

        # Кнопки
        self._make_btn(panel, "Очистить", self._clear)
        self._make_btn(panel, "Обрезать края", self._crop)
        self._make_btn(panel, "×2", lambda: self._downscale(2))
        self._make_btn(panel, "×3", lambda: self._downscale(3))
        self._make_btn(panel, "📷 Фото → ASCII", self._load_image, accent=ACCENT, hover=ACCENT_HOVER)
        self._make_btn(panel, "📷 Braille", self._load_image_braille, accent=ACCENT, hover=ACCENT_HOVER)
        self._make_btn(panel, "📄 Как текст", self._show_text)
        self._make_btn(panel, "💬 Копировать для Discord",
                       self._copy_for_discord, accent=DISCORD, hover=DISCORD_HOV)

        # ----- Холст -----
        canvas_wrap = tk.Frame(self.root, bg=BG_DARK)
        canvas_wrap.pack(fill="both", expand=True, padx=12, pady=(5, 0))

        self.canvas = tk.Canvas(
            canvas_wrap,
            width=self.cols * self.cell_w,
            height=self.rows * self.cell_h,
            bg=BG_CANVAS, highlightthickness=0,
            scrollregion=(0, 0, self.cols * self.cell_w, self.rows * self.cell_h),
        )
        self.canvas.pack(side="left", fill="both", expand=True)

        sb = tk.Scrollbar(canvas_wrap, orient="vertical", command=self.canvas.yview)
        sb.pack(side="right", fill="y")

        self.canvas.bind("<Button-1>", self._paint)
        self.canvas.bind("<B1-Motion>", self._paint)
        self.canvas.bind("<Button-3>", self._erase)
        self.canvas.bind("<B3-Motion>", self._erase)

        # ----- Статус-бар -----
        self.status = tk.Label(
            self.root, text="", anchor="w",
            font=("Consolas", 9), bg=BG_DARK, fg=FG_MUTED,
        )
        self.status.pack(fill="x", padx=12, pady=(0, 8))

    def _make_btn(self, parent, text, command, accent=None, hover=None):
        """Создаёт скруглённую кнопку с hover-эффектом."""
        bg = accent or BTN_BG
        hv = hover or BTN_HOVER
        fg = "white" if accent else FG_TEXT

        btn = RoundedButton(
            parent, text=text, command=command,
            bg=bg, hover=hv, fg=fg, radius=14,
        )
        btn.pack(side="left", padx=5, pady=2)
        return btn

    # ============ ЛОГИКА ============
    def _new_canvas(self):
        self.grid = [[" "] * self.cols for _ in range(self.rows)]
        self._redraw()
        self._update_status()

    def _clear(self):
        """Полная очистка: стирает холст И возвращает исходный размер."""
        # Считаем, сколько символов нарисовано
        filled = sum(1 for row in self.grid for ch in row if ch != " ")

        # разрешение на сброс
        if filled > 0:
            if not messagebox.askyesno(
                "Очистить холст?",
                f"На холсте нарисовано: {filled} символов.\n\n"
                f"Холст будет очищен и вернётся к размеру "
                f"{self.DEFAULT_COLS} × {self.DEFAULT_ROWS}.\n\n"
                f"Продолжить?"
            ):
                return

        
        self.cols = self.DEFAULT_COLS
        self.rows = self.DEFAULT_ROWS

        
        self._resize_canvas()
        self._new_canvas()

        
        self.canvas.yview_moveto(0)
        self.canvas.xview_moveto(0)

    def _update_char(self, event=None):
        val = self.char_entry.get()
        if val:
            self.current_char = val[0]

    def _on_char_set_change(self, *args):
        """Меняет активный набор символов."""
        global CHARS
        name = self.char_set_var.get()
        if name in CHAR_SETS:
            CHARS = CHAR_SETS[name]
            self.status.config(text=f"Набор символов: {name}   |   "
                                f"Холст: {self.cols} × {self.rows}")

    def _update_brush(self):
        self.brush_size = self.brush_size_var.get()

    def _paint(self, event):
        self._draw_at(event, self.current_char)

    def _erase(self, event):
        self._draw_at(event, " ")

    def _draw_at(self, event, char):
        cx = event.x // self.cell_w
        cy = event.y // self.cell_h
        size = self.brush_size_var.get()

        for dy in range(size):
            for dx in range(size):
                x, y = cx + dx, cy + dy
                if 0 <= x < self.cols and 0 <= y < self.rows:
                    self.grid[y][x] = char
        self._redraw()
        self._update_status()

    def _redraw(self):
        self.canvas.delete("all")

        # Лёгкая сетка 
        if self.cell_w >= 12 and self.cell_h >= 16:
            for x in range(self.cols + 1):
                self.canvas.create_line(
                    x * self.cell_w, 0, x * self.cell_w, self.rows * self.cell_h,
                    fill=GRID_COLOR,
                )
            for y in range(self.rows + 1):
                self.canvas.create_line(
                    0, y * self.cell_h, self.cols * self.cell_w, y * self.cell_h,
                    fill=GRID_COLOR,
                )

        # Символы
        for y in range(self.rows):
            for x in range(self.cols):
                ch = self.grid[y][x]
                if ch != " ":
                    self.canvas.create_text(
                        x * self.cell_w + self.cell_w // 2,
                        y * self.cell_h + self.cell_h // 2,
                        text=ch,
                        font=("Segoe UI Symbol", 12),
                        fill=FG_TEXT,
                    )

    def _update_status(self):
        filled = sum(1 for row in self.grid for ch in row if ch != " ")
        total = self.cols * self.rows
        self.status.config(
            text=f"Холст: {self.cols} × {self.rows}   |   "
                 f"Заполнено: {filled} / {total}   |   "
                 f"ЛКМ — рисовать, ПКМ — стереть"
        )

    def _resize_canvas(self):
        self.canvas.config(
            width=self.cols * self.cell_w,
            height=self.rows * self.cell_h,
            scrollregion=(0, 0, self.cols * self.cell_w, self.rows * self.cell_h),
        )

    # ============ ОБРЕЗКА КРАЁВ ============
    def _crop(self):
        min_x, min_y = self.cols, self.rows
        max_x, max_y = 0, 0

        for y in range(self.rows):
            for x in range(self.cols):
                if self.grid[y][x] != " ":
                    min_x = min(min_x, x)
                    min_y = min(min_y, y)
                    max_x = max(max_x, x)
                    max_y = max(max_y, y)

        if min_x > max_x:
            messagebox.showinfo("Пусто", "Холст пустой — нечего обрезать.")
            return

        new_cols = max_x - min_x + 1
        new_rows = max_y - min_y + 1
        new_grid = [[" "] * new_cols for _ in range(new_rows)]

        for y in range(new_rows):
            for x in range(new_cols):
                new_grid[y][x] = self.grid[min_y + y][min_x + x]

        self.grid = new_grid
        self.cols = new_cols
        self.rows = new_rows
        self._resize_canvas()
        self._redraw()
        self._update_status()

    # ============ УМЕНЬШЕНИЕ ============
    def _downscale(self, factor=2):
        new_cols = self.cols // factor
        new_rows = self.rows // factor
        new_grid = [[" "] * new_cols for _ in range(new_rows)]

        for y in range(new_rows):
            for x in range(new_cols):
                sy = y * factor + factor // 2
                sx = x * factor + factor // 2
                if 0 <= sy < self.rows and 0 <= sx < self.cols:
                    new_grid[y][x] = self.grid[sy][sx]

        self.grid = new_grid
        self.cols = new_cols
        self.rows = new_rows
        self._resize_canvas()
        self._redraw()
        self._update_status()

    # ============ ТЕКСТ ============
    def _show_text(self):
        lines = []
        for row in self.grid:
            line = "".join(ch if ch != " " else "\u00A0" for ch in row)
            lines.append(line)
        text = "\n".join(lines)

        win = tk.Toplevel(self.root)
        win.title("ASCII текст")
        win.geometry("820x620")
        win.configure(bg=BG_DARK)

        txt = tk.Text(
            win, wrap="none", font=("Consolas", 10),
            bg=BG_CANVAS, fg=FG_TEXT, insertbackground=ACCENT,
            relief="flat", padx=10, pady=10,
        )
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        txt.insert("1.0", text)

        bar = tk.Frame(win, bg=BG_DARK)
        bar.pack(fill="x", padx=10, pady=(0, 10))

        tk.Label(bar, text=f"Символов: {len(text)}", font=("Consolas", 10),
                 bg=BG_DARK, fg=FG_MUTED).pack(side="left")

        def copy():
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("Готово", "Скопировано в буфер обмена!")

        self._make_btn(bar, "📋 Скопировать всё", copy, accent=ACCENT, hover=ACCENT_HOVER)

    # ============ DISCORD ============
    def _copy_for_discord(self):
        lines = []
        for row in self.grid:
            line = "".join(ch if ch != " " else "\u00A0" for ch in row)
            lines.append(line)

        art = "\n".join(lines)
        text = f"```\n{art}\n```"
        length = len(text)

        self.root.clipboard_clear()
        self.root.clipboard_append(text)

        if length <= 2000:
            messagebox.showinfo(
                "Скопировано ✅",
                f"Символов: {length} / 2000\n\n"
                f"Открывай Discord → Ctrl+V → отправляй!"
            )
        elif length <= 4000:
            messagebox.showinfo(
                "Скопировано ⚠️",
                f"Символов: {length} / 2000\n\n"
                f"Влезет только с Nitro."
            )
        else:
            messagebox.showwarning(
                "Слишком большой ❌",
                f"Символов: {length}\n\n"
                f"Превышает лимит Discord (2000).\n"
                f"Уменьши арт кнопкой «×2» или «Обрезать края»."
            )

    # ============ ФОТО ============
    def _load_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if not path:
            return

        img = Image.open(path)
        img = ImageOps.exif_transpose(img)
        img = img.convert("L")
        img = img.resize((self.cols, self.rows))

        pixels = img.load()
        n = len(CHARS) - 1

        for y in range(self.rows):
            for x in range(self.cols):
                brightness = pixels[x, y]
                idx = int((brightness / 255) * n)
                self.grid[y][x] = CHARS[idx]

        self._redraw()
        self._update_status()
        messagebox.showinfo("Готово", "Фото преобразовано! Нажми «Как текст» или «Копировать для Discord».")

    def _load_image_braille(self):
        """Импорт фото в Braille-стиле — в 8 раз детальнее ASCII."""
        path = filedialog.askopenfilename(
            filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if not path:
            return

        try:
            img = Image.open(path)
            img = ImageOps.exif_transpose(img)
            img = img.convert("L")  # ч/б
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")
            return

        # Каждый символ Брайля = 2 колонки × 4 строки пикселей
        target_w = self.cols * 2
        target_h = self.rows * 4
        img = img.resize((target_w, target_h))

        pixels = img.load()
        threshold = 128  # порог: темнее 128 → точка есть

        for cy in range(self.rows):
            for cx in range(self.cols):
                block = [[0] * 2 for _ in range(4)]
                for py in range(4):
                    for px in range(2):
                        gx = cx * 2 + px
                        gy = cy * 4 + py
                        if pixels[gx, gy] < threshold:
                            block[py][px] = 1
                self.grid[cy][cx] = self._pixel_block_to_braille(block)

        self._redraw()
        self._update_status()
        messagebox.showinfo(
            "Готово! 🎨",
            f"Braille-арт построен.\n\n"
            f"Холст: {self.cols} × {self.rows}\n"
            f"Реальное разрешение: {self.cols * 2} × {self.rows * 4} пикселей\n\n"
            f"💡 Для Steam профиля: нажми «×2», потом «Обрезать края» "
            f"и копируй через «📄 Как текст»."
        )

    def _pixel_block_to_braille(self, block):
        """Превращает блок 2×4 (0/1) в один символ Брайля.
        
        block[y][x] — 1 = точка включена, 0 = выключена.
        Порядок: y от 0 (верх) до 3 (низ), x от 0 (лево) до 1 (право).
        """
        code = 0x2800
        for dx, dy, bit in BRAILLE_MAP:
            if block[dy][dx]:
                code |= bit
        return chr(code)


if __name__ == "__main__":
    root = tk.Tk()
    app = AsciiPaint(root)
    root.mainloop()