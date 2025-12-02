import subprocess
import json
import os
from datetime import datetime

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import scrolledtext


class MetaEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Metadata Editor")
        self.root.geometry("900x750")
        self.root.minsize(800, 650)
        self.root.resizable(True, True)

        self.selected_files = []
        self.current_meta = {}

        # ---- FRAME FIȘIERE ----
        files_frame = tk.LabelFrame(root, text="Fișiere imagine", padx=10, pady=10)
        files_frame.pack(fill="x", padx=10, pady=10)

        self.files_label = tk.Label(files_frame, text="Niciun fișier selectat")
        self.files_label.pack(anchor="w")

        self.current_file_label = tk.Label(files_frame, text="Meta pentru: -")
        self.current_file_label.pack(anchor="w")

        select_btn = tk.Button(files_frame, text="Selectează imagini",
                               command=self.select_files)
        select_btn.pack(pady=5)

        # ---- FRAME METADATA EDITABILE ----
        meta_frame = tk.LabelFrame(
            root,
            text="Meta date de setat (se aplică la toate fișierele selectate)",
            padx=10,
            pady=10,
        )
        meta_frame.pack(fill="x", padx=10, pady=5)

        # Titlu
        tk.Label(meta_frame, text="Titlu (Title, ex: „Gresie porțelanată 60x60”):").grid(
            row=0, column=0, sticky="w"
        )
        self.title_entry = tk.Entry(meta_frame, width=55)
        self.title_entry.grid(row=0, column=1, pady=2, sticky="w")

        # Autor
        tk.Label(meta_frame, text="Autor (Artist/Creator, ex: „CeraMall Studio”):").grid(
            row=1, column=0, sticky="w"
        )
        self.author_entry = tk.Entry(meta_frame, width=55)
        self.author_entry.grid(row=1, column=1, pady=2, sticky="w")

        # Descriere
        tk.Label(meta_frame, text="Descriere (ex: „Fotografie produs pentru site”):").grid(
            row=2, column=0, sticky="w"
        )
        self.desc_entry = tk.Entry(meta_frame, width=55)
        self.desc_entry.grid(row=2, column=1, pady=2, sticky="w")

        # Cuvinte cheie
        tk.Label(
            meta_frame,
            text="Keywords (ex: „gresie, faianta, parchet, baie”):",
        ).grid(row=3, column=0, sticky="w")
        self.keywords_entry = tk.Entry(meta_frame, width=55)
        self.keywords_entry.grid(row=3, column=1, pady=2, sticky="w")

        # Drepturi de autor
        tk.Label(
            meta_frame,
            text='Copyright (ex: "© 2025 CeraMall"):',
        ).grid(row=4, column=0, sticky="w")
        self.copyright_entry = tk.Entry(meta_frame, width=55)
        self.copyright_entry.grid(row=4, column=1, pady=2, sticky="w")

        # Dată originală (opțional)
        tk.Label(
            meta_frame,
            text="Data originală (YYYY:MM:DD HH:MM:SS, ex: 2025:12:02 10:15:00):",
        ).grid(row=5, column=0, sticky="w")
        self.date_entry = tk.Entry(meta_frame, width=30)
        self.date_entry.grid(row=5, column=1, pady=2, sticky="w")
        date_btn = tk.Button(meta_frame, text="Data curentă", command=self.set_current_date)
        date_btn.grid(row=5, column=2, padx=5, sticky="w")

        # ---- FRAME META COMPLETĂ (EDITABILĂ) ----
        full_meta_frame = tk.LabelFrame(
            root, text="Meta date complete (editabile – avansat)", padx=10, pady=10
        )
        full_meta_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.apply_full_meta_var = tk.BooleanVar(value=False)
        self.apply_full_meta_check = tk.Checkbutton(
            full_meta_frame,
            text=(
                "Aplică și modificările din lista completă de meta date "
                "(Title/Author/Descriere/Keywords/Date/Copyright se iau din câmpurile de sus)"
            ),
            variable=self.apply_full_meta_var,
        )
        self.apply_full_meta_check.pack(anchor="w", pady=(0, 5))

        self.meta_text = scrolledtext.ScrolledText(
            full_meta_frame, wrap="word", width=100, height=16
        )
        self.meta_text.pack(fill="both", expand=True)
        self.meta_text.insert(
            "1.0",
            "Aici vor apărea meta datele complete după ce selectezi o imagine.\n"
            "Format: NumeTag = valoare (o meta pe linie). Poți edita valorile.",
        )

        # ---- BUTOANE ----
        btn_frame = tk.Frame(root)
        btn_frame.pack(fill="x", padx=10, pady=10)

        button_font = ("Segoe UI", 10, "bold")

        apply_btn = tk.Button(
            btn_frame,
            text="Scrie meta date în fișiere",
            command=self.apply_metadata,
            font=button_font,
            width=26,
        )
        apply_btn.pack(side="left", padx=(0, 10), ipady=6)

        clear_btn = tk.Button(
            btn_frame,
            text="Golește câmpurile",
            command=self.clear_fields,
            font=button_font,
            width=20,
        )
        clear_btn.pack(side="left", padx=(0, 10), ipady=6)

        quit_btn = tk.Button(
            btn_frame,
            text="Închide",
            command=root.quit,
            font=button_font,
            width=12,
        )
        quit_btn.pack(side="right", ipady=6)

        # Status bar
        self.status_label = tk.Label(root, text="", anchor="w")
        self.status_label.pack(fill="x", padx=10, pady=(0, 5))

    # ---------- UTILITARE UI ----------
    def select_files(self):
        filetypes = [
            ("Imagini", "*.jpg *.jpeg *.png *.tif *.tiff *.bmp *.gif *.heic *.webp"),
            ("Toate fișierele", "*.*"),
        ]
        files = filedialog.askopenfilenames(
            title="Selectează imaginile",
            filetypes=filetypes,
        )
        if files:
            self.selected_files = list(files)
            self.files_label.config(text=f"{len(self.selected_files)} fișier(e) selectat(e)")
            self.status_label.config(text="")
            # Încarcăm meta pentru primul fișier selectat
            self.load_metadata_for_file(self.selected_files[0])
        else:
            self.selected_files = []
            self.files_label.config(text="Niciun fișier selectat")
            self.current_file_label.config(text="Meta pentru: -")
            self.clear_fields()
            self.clear_meta_view()

    def clear_fields(self):
        self.title_entry.delete(0, tk.END)
        self.author_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.keywords_entry.delete(0, tk.END)
        self.copyright_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.status_label.config(text="Câmpuri golite.")

    def clear_meta_view(self):
        self.meta_text.delete("1.0", tk.END)
        self.meta_text.insert(
            "1.0",
            "Meta datele nu sunt încărcate.\n"
            "Format: NumeTag = valoare (o meta pe linie).",
        )
        self.current_meta = {}

    def set_current_date(self):
        """Setează în câmpul de dată data și ora curentă, în formatul cerut."""
        now_str = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, now_str)

    # ---------- CITIRE META ----------
    def load_metadata_for_file(self, filepath):
        """Citește meta datele complete pentru un fișier și actualizează UI-ul."""
        try:
            result = subprocess.run(
                ["exiftool", "-j", filepath],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except FileNotFoundError:
            messagebox.showerror(
                "Eroare",
                "Nu am găsit 'exiftool'.\n"
                "Asigură-te că este instalat și adăugat în PATH\n"
                "sau că fișierul exiftool.exe este în același folder cu acest script.",
            )
            return

        if result.returncode != 0:
            messagebox.showerror(
                "Eroare la citirea meta datelor",
                result.stderr or "Eroare necunoscută.",
            )
            return

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            messagebox.showerror("Eroare", "Nu am putut interpreta ieșirea JSON de la exiftool.")
            return

        if not data:
            messagebox.showwarning("Atenție", "Nu am găsit meta date pentru acest fișier.")
            return

        meta = data[0]
        self.current_meta = meta
        filename = os.path.basename(filepath)
        self.current_file_label.config(text=f"Meta pentru: {filename}")

        # Pre-populăm câmpurile „de bază”
        def set_entry(entry_widget, value):
            entry_widget.delete(0, tk.END)
            if value is not None:
                entry_widget.insert(0, str(value))

        # Titlu
        title = meta.get("Title") or meta.get("ObjectName") or meta.get("XPTitle")
        set_entry(self.title_entry, title)

        # Autor
        author = meta.get("Artist") or meta.get("Creator") or meta.get("XPAuthor")
        set_entry(self.author_entry, author)

        # Descriere
        desc = meta.get("Description") or meta.get("ImageDescription") or meta.get(
            "XPComment"
        )
        set_entry(self.desc_entry, desc)

        # Keywords
        keywords = meta.get("Keywords")
        if isinstance(keywords, list):
            keywords_str = ", ".join(str(k) for k in keywords)
        else:
            keywords_str = keywords
        set_entry(self.keywords_entry, keywords_str)

        # Copyright
        copyright_text = meta.get("Copyright")
        set_entry(self.copyright_entry, copyright_text)

        # Dată originală (fallback și pe CreateDate / ModifyDate dacă lipsesc)
        date_original = (
            meta.get("DateTimeOriginal")
            or meta.get("CreateDate")
            or meta.get("ModifyDate")
        )
        set_entry(self.date_entry, date_original)

        # Afișăm meta completă în zona de jos – format simplu Tag = valoare
        self.meta_text.delete("1.0", tk.END)
        lines = []
        for tag in sorted(meta.keys()):
            value = meta[tag]
            lines.append(f"{tag} = {value}")
        self.meta_text.insert("1.0", "\n".join(lines))

        self.status_label.config(text=f"Meta date încărcate pentru {filename}.")

    # ---------- SCRIERE META ----------
    def apply_metadata(self):
        if not self.selected_files:
            messagebox.showwarning(
                "Atenție", "Te rog selectează cel puțin un fișier imagine."
            )
            return

        title = self.title_entry.get().strip()
        author = self.author_entry.get().strip()
        desc = self.desc_entry.get().strip()
        keywords = self.keywords_entry.get().strip()
        copyright_text = self.copyright_entry.get().strip()
        date_original = self.date_entry.get().strip()

        if not any([title, author, desc, keywords, copyright_text, date_original]) and not self.apply_full_meta_var.get():
            messagebox.showwarning(
                "Atenție",
                "Nu ai completat niciun câmp de meta date și nici nu ai selectat aplicarea "
                "modificărilor din lista completă.",
            )
            return

        # Construim comanda exiftool
        cmd = ["exiftool"]

        # Titlu - setăm mai multe tag-uri pentru compatibilitate
        if title:
            cmd.append(f"-Title={title}")
            cmd.append(f"-XPTitle={title}")
            cmd.append(f"-ObjectName={title}")

        # Autor
        if author:
            cmd.append(f"-Artist={author}")
            cmd.append(f"-XPAuthor={author}")
            cmd.append(f"-Creator={author}")

        # Descriere
        if desc:
            cmd.append(f"-ImageDescription={desc}")
            cmd.append(f"-XPComment={desc}")
            cmd.append(f"-Description={desc}")

        # Keywords – separem prin virgulă
        if keywords:
            # golim mai întâi keywords, apoi adăugăm
            cmd.append("-Keywords=")
            for kw in [k.strip() for k in keywords.split(",") if k.strip()]:
                cmd.append(f"-Keywords={kw}")

        # Copyright
        if copyright_text:
            cmd.append(f"-Copyright={copyright_text}")

        # Data originală
        if date_original:
            cmd.append(f"-DateTimeOriginal={date_original}")

        # Modificări din meta completă (dacă e bifat)
        if self.apply_full_meta_var.get():
            raw = self.meta_text.get("1.0", tk.END).strip()
            if raw:
                reserved = {
                    "Title",
                    "XPTitle",
                    "ObjectName",
                    "Artist",
                    "XPAuthor",
                    "Creator",
                    "ImageDescription",
                    "XPComment",
                    "Description",
                    "Keywords",
                    "Copyright",
                    "DateTimeOriginal",
                    "CreateDate",
                    "ModifyDate",
                }

                for line in raw.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        # Linie invalidă; o ignorăm
                        continue
                    tag, value = line.split("=", 1)
                    tag = tag.strip()
                    value = value.strip()
                    if not tag:
                        continue
                    if tag in reserved:
                        # pentru aceste tag-uri folosim câmpurile de sus
                        continue
                    # dacă valoarea e goală, ștergem tag-ul
                    if value == "":
                        cmd.append(f"-{tag}=")
                    else:
                        cmd.append(f"-{tag}={value}")

        # Suprascrie direct fișierele (fără ._original)
        cmd.append("-overwrite_original")

        # Adăugăm fișierele la final
        cmd.extend(self.selected_files)

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except FileNotFoundError:
            messagebox.showerror(
                "Eroare",
                "Nu am găsit 'exiftool'.\n"
                "Asigură-te că este instalat și adăugat în PATH\n"
                "sau că fișierul exiftool.exe este în același folder cu acest script.",
            )
            return

        if result.returncode == 0:
            messagebox.showinfo(
                "Succes",
                "Meta datele au fost actualizate cu succes pentru toate fișierele selectate.",
            )
            self.status_label.config(text="Meta date scrise cu succes.")
        else:
            messagebox.showerror(
                "Eroare la exiftool", result.stderr or "Eroare necunoscută."
            )
            self.status_label.config(
                text="A apărut o eroare. Verifică mesajul ExifTool."
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = MetaEditorApp(root)
    root.mainloop()
