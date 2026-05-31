"""
BuildAdvisor – GUI (Tkinter)
A clean desktop interface for estimating construction costs.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from predict import predict_cost


# ── Palette ───────────────────────────────────────────────────────────────────
BG          = "#0f1117"
CARD        = "#1a1d27"
ACCENT      = "#4f8ef7"
ACCENT2     = "#7b5ea7"
TEXT        = "#e8eaf6"
TEXT_DIM    = "#8892a4"
SUCCESS     = "#43d98b"
BORDER      = "#2a2d3e"
INPUT_BG    = "#22263a"
FONT_BODY   = ("Segoe UI", 11)
FONT_LABEL  = ("Segoe UI", 10)
FONT_TITLE  = ("Segoe UI", 22, "bold")
FONT_SUB    = ("Segoe UI", 11)
FONT_RESULT = ("Segoe UI", 26, "bold")


class BuildAdvisorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BuildAdvisor – Cost Estimator")
        self.configure(bg=BG)
        self.resizable(False, False)
        self._build_ui()
        self._center()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header
        header = tk.Frame(self, bg=BG, pady=28)
        header.pack(fill="x", padx=36)

        tk.Label(header, text="🏗️  BuildAdvisor", font=FONT_TITLE,
                 bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(header, text="Construction Cost Estimator · Pakistan",
                 font=FONT_SUB, bg=BG, fg=TEXT_DIM).pack(anchor="w", pady=(2, 0))

        # ── Card
        card = tk.Frame(self, bg=CARD, bd=0, relief="flat",
                        highlightthickness=1, highlightbackground=BORDER)
        card.pack(padx=36, pady=(0, 16), fill="both")

        inner = tk.Frame(card, bg=CARD, padx=28, pady=24)
        inner.pack(fill="both")

        # Two-column grid
        left  = tk.Frame(inner, bg=CARD)
        right = tk.Frame(inner, bg=CARD)
        left.grid(row=0, column=0, sticky="n", padx=(0, 24))
        right.grid(row=0, column=1, sticky="n")

        # ── Left column
        self.area_var     = tk.StringVar()
        self.floors_var   = tk.StringVar()
        self.rooms_var    = tk.StringVar()
        self.bath_var     = tk.StringVar()
        self.loc_var      = tk.DoubleVar(value=1.0)

        self._field(left, 0, "Total Area (sqft)", self.area_var,     placeholder="e.g. 1200")
        self._field(left, 1, "Number of Floors",  self.floors_var,   placeholder="e.g. 2")
        self._field(left, 2, "Number of Rooms",   self.rooms_var,    placeholder="e.g. 3")
        self._field(left, 3, "Number of Bathrooms", self.bath_var,   placeholder="e.g. 2")
        self._slider(left, 4, "Location Factor",  self.loc_var, 1.0, 1.3)

        # ── Right column
        self.constr_var  = tk.StringVar(value="residential")
        self.quality_var = tk.StringVar(value="standard")
        self.struct_var  = tk.StringVar(value="brick")

        self._radio_group(right, 0, "Construction Type",
                          [("Residential", "residential"), ("Commercial", "commercial")],
                          self.constr_var)
        self._radio_group(right, 1, "Quality Level",
                          [("Basic", "basic"), ("Standard", "standard"), ("Premium", "premium")],
                          self.quality_var)
        self._radio_group(right, 2, "Structure Type",
                          [("Brick", "brick"), ("Concrete", "concrete"), ("Steel", "steel")],
                          self.struct_var)

        # ── Estimate button
        btn_frame = tk.Frame(self, bg=BG, pady=10)
        btn_frame.pack()
        tk.Button(
            btn_frame, text="  Calculate Cost  ",
            font=("Segoe UI", 13, "bold"),
            bg=ACCENT, fg="white", activebackground="#3a6fd8",
            activeforeground="white", relief="flat", cursor="hand2",
            bd=0, padx=24, pady=12,
            command=self._calculate
        ).pack()

        # ── Result panel
        self.result_frame = tk.Frame(self, bg=BG, pady=4)
        self.result_frame.pack(padx=36, pady=(0, 32), fill="x")

        self.result_label = tk.Label(
            self.result_frame, text="", font=FONT_RESULT,
            bg=BG, fg=SUCCESS
        )
        self.result_label.pack()

        self.result_sub = tk.Label(
            self.result_frame, text="", font=FONT_LABEL,
            bg=BG, fg=TEXT_DIM
        )
        self.result_sub.pack()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _field(self, parent, row, label, var, placeholder=""):
        tk.Label(parent, text=label, font=FONT_LABEL, bg=CARD, fg=TEXT_DIM,
                 anchor="w").grid(row=row*2, column=0, sticky="w", pady=(10, 2))
        entry = tk.Entry(parent, textvariable=var, font=FONT_BODY,
                         bg=INPUT_BG, fg=TEXT, insertbackground=TEXT,
                         relief="flat", bd=0, width=22,
                         highlightthickness=1, highlightbackground=BORDER,
                         highlightcolor=ACCENT)
        entry.grid(row=row*2+1, column=0, sticky="ew", ipady=8, padx=2)
        if placeholder and not var.get():
            entry.insert(0, placeholder)
            entry.config(fg=TEXT_DIM)
            entry.bind("<FocusIn>",  lambda e, en=entry, v=var, p=placeholder: self._clear_ph(en, v, p))
            entry.bind("<FocusOut>", lambda e, en=entry, v=var, p=placeholder: self._restore_ph(en, v, p))

    def _clear_ph(self, entry, var, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(fg=TEXT)

    def _restore_ph(self, entry, var, placeholder):
        if not entry.get():
            entry.insert(0, placeholder)
            entry.config(fg=TEXT_DIM)

    def _slider(self, parent, row, label, var, from_, to_):
        tk.Label(parent, text=label, font=FONT_LABEL, bg=CARD, fg=TEXT_DIM,
                 anchor="w").grid(row=row*2, column=0, sticky="w", pady=(10, 2))

        sf = tk.Frame(parent, bg=CARD)
        sf.grid(row=row*2+1, column=0, sticky="ew", padx=2)

        scale = tk.Scale(sf, variable=var, from_=from_, to=to_,
                         resolution=0.05, orient="horizontal",
                         bg=CARD, fg=TEXT, troughcolor=INPUT_BG,
                         highlightthickness=0, sliderrelief="flat",
                         length=200, showvalue=False,
                         command=lambda v: val_lbl.config(text=f"{float(v):.2f}"))
        scale.pack(side="left")
        val_lbl = tk.Label(sf, text=f"{from_:.2f}", font=FONT_BODY,
                           bg=CARD, fg=ACCENT, width=5)
        val_lbl.pack(side="left", padx=(8, 0))

    def _radio_group(self, parent, group_row, label, options, var):
        tk.Label(parent, text=label, font=FONT_LABEL, bg=CARD, fg=TEXT_DIM,
                 anchor="w").grid(row=group_row*4, column=0, columnspan=2,
                                  sticky="w", pady=(14, 4))
        for i, (text, value) in enumerate(options):
            tk.Radiobutton(
                parent, text=text, variable=var, value=value,
                font=FONT_BODY, bg=CARD, fg=TEXT,
                activebackground=CARD, activeforeground=ACCENT,
                selectcolor=INPUT_BG, relief="flat",
                indicatoron=True, cursor="hand2"
            ).grid(row=group_row*4+1+i, column=0, sticky="w", padx=8)

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _get_entry(self, var, label, cast, placeholder=""):
        raw = var.get().strip()
        if raw == placeholder or raw == "":
            raise ValueError(f"'{label}' is required.")
        return cast(raw)

    def _calculate(self):
        self.result_label.config(text="")
        self.result_sub.config(text="")
        try:
            area      = self._get_entry(self.area_var,   "Total Area",           float, "e.g. 1200")
            floors    = self._get_entry(self.floors_var,  "Number of Floors",     int,   "e.g. 2")
            rooms     = self._get_entry(self.rooms_var,   "Number of Rooms",      int,   "e.g. 3")
            bathrooms = self._get_entry(self.bath_var,    "Number of Bathrooms",  int,   "e.g. 2")
            loc       = round(self.loc_var.get(), 2)

            if area <= 0:     raise ValueError("Area must be > 0")
            if floors < 1:    raise ValueError("Floors must be ≥ 1")
            if rooms < 1:     raise ValueError("Rooms must be ≥ 1")
            if bathrooms < 1: raise ValueError("Bathrooms must be ≥ 1")

        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
            return

        result = predict_cost({
            "total_area_sqft":     area,
            "number_of_floors":    floors,
            "number_of_rooms":     rooms,
            "number_of_bathrooms": bathrooms,
            "location_factor":     loc,
            "construction_type":   self.constr_var.get(),
            "quality_level":       self.quality_var.get(),
            "structure_type":      self.struct_var.get(),
        })

        self.result_label.config(text=result["formatted"])
        self.result_sub.config(
            text=f"{self.quality_var.get().title()} {self.struct_var.get()} · "
                 f"{self.constr_var.get().title()} · {area:,.0f} sqft · "
                 f"{floors} floor(s) · Location ×{loc:.2f}"
        )


if __name__ == "__main__":
    app = BuildAdvisorApp()
    app.mainloop()
