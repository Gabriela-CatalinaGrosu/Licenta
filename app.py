import csv
import os
import json
from music21 import converter, corpus
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk
import subprocess
from analizare_note import analiza_file
from pattern import find_pattern
from segmentare import segmentare
from note import extrage_note_muzicale

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Analysis Tool")
        self.root.geometry("1200x800")

        self.part = None  # Partitura
        self.output_dir = "output"
        self.input_file = None
        self.files_by_folder = {}  # Dicționar pentru toate fișierele
        self.current_display_path = None
        self.notes = False  # Starea analizei inițiale a notelor
        self.notes_analyzed = False  # Starea analizei detaliate a notelor
        self.pattern_analyzed = False  # Starea analizei pattern-urilor
        self.segmentation_done = False  # Starea analizei segmentării

        self.csv_file_notes = None
        self.output_dir_notes = None
        self.output_dir_pattern = None
        self.output_dir_analyze_notes = None
        self.output_dir_seg = None
        self.generated_files = {  # Dicționar pentru a urmări fișierele generate de fiecare analiză
            "notes": set(),
            "notes_detail": set(),
            "pattern": set(),
            "segmentation": set()
        }

        self.create_widgets()

    def create_widgets(self):
        """
        Creează widget-urile principale ale aplicației.
        """
        # Frame principal cu grid
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Frame pentru selecția fișierului
        self.file_frame = tk.Frame(self.main_frame)
        self.file_frame.grid(row=0, column=0, columnspan=2, pady=10, sticky="ew")

        self.file_label = tk.Label(self.file_frame, text="No file selected")
        self.file_label.pack(side=tk.LEFT, padx=5)

        self.select_button = tk.Button(self.file_frame, text="Select MusicXML/MIDI File", command=self.select_file)
        self.select_button.pack(side=tk.LEFT, padx=5)

        # Frame pentru analiza
        self.action_frame = tk.Frame(self.main_frame)
        self.action_frame.grid(row=1, column=0, columnspan=2, pady=5, sticky="ew")

        self.analyze_notes_button = tk.Button(self.action_frame, text="Notes", command=self.analyze_notes, state=tk.DISABLED)
        self.analyze_notes_button.pack(side=tk.LEFT, padx=5)

        self.analyze_segmentation_button = tk.Button(self.action_frame, text="Analyze Segmentation", command=self.analyze_segmentation, state=tk.DISABLED)
        self.analyze_segmentation_button.pack(side=tk.LEFT, padx=5)

        self.scroll_label = tk.Label(self.action_frame, text="Scroll down to see all buttons ↓", fg="blue")
        self.scroll_label.pack(side=tk.LEFT, padx=5)

        # Frame pentru butoane cu scrollbar vertical
        self.button_frame = tk.Frame(self.main_frame)
        self.button_frame.grid(row=2, column=0, columnspan=2, pady=5, sticky="nsew")

        self.button_canvas = tk.Canvas(self.button_frame)
        self.button_scrollbar = tk.Scrollbar(self.button_frame, orient=tk.VERTICAL, command=self.button_canvas.yview)
        self.button_scrollable_frame = tk.Frame(self.button_canvas)

        self.button_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.button_canvas.configure(scrollregion=self.button_canvas.bbox("all"))
        )

        self.button_canvas.create_window((0, 0), window=self.button_scrollable_frame, anchor="nw")
        self.button_canvas.configure(yscrollcommand=self.button_scrollbar.set)

        self.button_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.button_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Frame unic pentru afișare (CSV, JSON, PNG, TXT, sau partitură)
        self.display_frame = tk.Frame(self.main_frame)
        self.display_frame.grid(row=3, column=0, columnspan=2, pady=5, sticky="nsew")

        self.display_label = tk.Label(self.display_frame)
        self.display_label.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(self.display_frame, columns=("Field1", "Field2", "Field3"), show="headings")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Bind pentru redimensionarea afișării
        self.display_frame.bind("<Configure>", self.resize_display)

        # Configurare grid
        self.main_frame.grid_rowconfigure(2, weight=0, minsize=150)
        self.main_frame.grid_rowconfigure(3, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

    def select_file(self):
        """
        Deschide un dialog pentru a selecta un fișier MusicXML sau MIDI.
        """

        file_path = filedialog.askopenfilename(filetypes=[("MusicXML/MIDI Files", "*.xml *.mid *.midi"), ("All Files", "*.*")])
        if file_path:
            self.file_label.config(text=os.path.basename(file_path))
            self.input_file = file_path
            self.analyze_notes_button.config(state=tk.NORMAL)
            self.analyze_segmentation_button.config(state=tk.NORMAL)
            self.notes = False
            self.notes_analyzed = False
            self.pattern_analyzed = False
            self.segmentation_done = False
            self.generated_files = {
                "notes": set(),
                "notes_detail": set(),
                "pattern": set(),
                "segmentation": set()
            }

    def analyze_notes(self):
        """
        Rulează analiza notelor muzicale din fișierul selectat.
        """

        if not self.input_file:
            messagebox.showerror("Error", "No file selected!")
            return

        if not self.notes:
            try:
                # Încarcă fișierul
                if not self.input_file.endswith(('.xml', '.mid', '.midi')):
                    messagebox.showerror("Error", "File must be in MusicXML (.xml) or MIDI (.mid, .midi) format!")
                    return

                try:
                    self.part = converter.parse(self.input_file)
                except Exception as e:
                    try:
                        self.part = corpus.parse(self.input_file)
                    except Exception as e:
                        messagebox.showerror("Error", f"Error loading file '{self.input_file}': {e}")
                        return

                name = os.path.splitext(os.path.basename(self.input_file))[0]
                self.output_dir = os.path.join("output", name)
                os.makedirs(self.output_dir, exist_ok=True)

                # Salvează partitura ca MusicXML temporar
                musicxml_path = os.path.join(self.output_dir, "partitura_temp.xml")
                self.part.write('musicxml', fp=musicxml_path)

                # Rulează analiza notelor
                self.csv_file_notes, self.output_dir_notes = extrage_note_muzicale(self.part, name, self.output_dir)
                self.notes = True
                # Adaugă toate fișierele din output_dir_notes și subdirectoare
                for root, _, files in os.walk(self.output_dir_notes):
                    for file in files:
                        if file.endswith((".csv", ".png", ".json", ".txt")):
                            self.generated_files["notes"].add(os.path.relpath(os.path.join(root, file), self.output_dir))

                # Adaugă butoane suplimentare
                self.add_analysis_buttons()

                # Scanează fișierele și creează butoane doar pentru analiza notelor
                self.scan_files(self.output_dir_notes, "notes")
                self.create_buttons()

                messagebox.showinfo("Success", "Notes analysis completed. Use the buttons to view results or proceed with further analysis.")
            except Exception as e:
                messagebox.showerror("Error", f"Analysis failed: {e}")
        else:
            messagebox.showinfo("Info", "Notes analysis already completed. Displaying existing results.")
            self.scan_files(self.output_dir_notes, "notes")
            self.create_buttons()

    def analyze_segmentation(self):
        """
        Rulează analiza segmentării partiturii.
        """

        if not self.input_file:
            messagebox.showerror("Error", "No file selected!")
            return

        if not self.segmentation_done:
            try:
                # Încarcă fișierul
                if not self.input_file.endswith(('.xml', '.mid', '.midi')):
                    messagebox.showerror("Error", "File must be in MusicXML (.xml) or MIDI (.mid, .midi) format!")
                    return

                try:
                    self.part = converter.parse(self.input_file)
                except Exception as e:
                    try:
                        self.part = corpus.parse(self.input_file)
                    except Exception as e:
                        messagebox.showerror("Error", f"Error loading file '{self.input_file}': {e}")
                        return

                name = os.path.splitext(os.path.basename(self.input_file))[0]
                self.output_dir = os.path.join("output", name)
                os.makedirs(self.output_dir, exist_ok=True)

                # Salvează partitura ca MusicXML temporar
                musicxml_path = os.path.join(self.output_dir, "partitura_temp.xml")
                self.part.write('musicxml', fp=musicxml_path)

                # Rulează analiza segmentării
                self.output_dir_seg = segmentare(self.part, self.output_dir)
                self.segmentation_done = True
                # Adaugă toate fișierele din output_dir_seg și subdirectoare
                for root, _, files in os.walk(self.output_dir_seg):
                    for file in files:
                        if file.endswith((".csv", ".png", ".json", ".txt")):
                            self.generated_files["segmentation"].add(os.path.relpath(os.path.join(root, file), self.output_dir))

                # Scanează fișierele și creează butoane
                self.scan_files(self.output_dir_seg, "segmentation")
                self.create_buttons()

                messagebox.showinfo("Success", "Segmentation analysis completed. Use the buttons to view results.")
            except Exception as e:
                messagebox.showerror("Error", f"Analysis segmentation failed: {e}")
        else:
            messagebox.showinfo("Info", "Segmentation analysis already completed. Displaying existing results.")
            self.scan_files(self.output_dir_seg, "segmentation")
            self.create_buttons()

    def add_analysis_buttons(self):
        """
        Adaugă butoanele pentru analize suplimentare după analiza inițială a notelor.
        """
        # Șterge butoanele existente din action_frame (cu excepția butoanelor inițiale)
        for widget in self.action_frame.winfo_children():
            if widget not in (self.analyze_notes_button, self.analyze_segmentation_button, self.scroll_label):
                widget.destroy()

        # Adaugă butoanele pentru analize suplimentare
        self.analyze_notes_detail_button = tk.Button(self.action_frame, text="Analyze Notes in Detail", command=self.analyze_notes_detail)
        self.analyze_notes_detail_button.pack(side=tk.LEFT, padx=5)

        self.analyze_pattern_button = tk.Button(self.action_frame, text="Analyze Pattern", command=self.analyze_pattern)
        self.analyze_pattern_button.pack(side=tk.LEFT, padx=5)

    def analyze_notes_detail(self):
        """
        Rulează analiza detaliată a notelor muzicale din fișierul selectat.
        """

        if not self.input_file or not self.part:
            messagebox.showerror("Error", "No file or partitura loaded!")
            return

        if not self.notes_analyzed:
            try:
                name = os.path.splitext(os.path.basename(self.input_file))[0]
                self.output_dir_analyze_notes = analiza_file(self.csv_file_notes, self.output_dir_notes)
                self.notes_analyzed = True
                # Adaugă toate fișierele din output_dir_analyze_notes și subdirectoare
                for root, _, files in os.walk(self.output_dir_analyze_notes):
                    for file in files:
                        if file.endswith((".csv", ".png", ".json", ".txt")):
                            self.generated_files["notes_detail"].add(os.path.relpath(os.path.join(root, file), self.output_dir))
                messagebox.showinfo("Success", "Detailed notes analysis completed.")
            except Exception as e:
                messagebox.showerror("Error", f"Detailed analysis failed: {e}")
        else:
            messagebox.showinfo("Info", "Detailed notes analysis already completed. Displaying existing results.")

        # Actualizează butoanele cu fișierele existente pentru analiza detaliată
        self.scan_files(self.output_dir_analyze_notes, "notes_detail")
        self.create_buttons()

    def analyze_pattern(self):
        """
        Rulează analiza pattern-urilor din partitura încărcată.
        """
        if not self.input_file or not self.part:
            messagebox.showerror("Error", "No file or partitura loaded!")
            return

        if not self.pattern_analyzed:
            try:
                # Implementare simplă a analizei pattern-urilor
                name = os.path.splitext(os.path.basename(self.input_file))[0]
                from vizualizare_pattern import generate_all_graphics  # Ajustează calea dacă este necesar
                total_duration = int(self.part.flat.quarterLength)
                output_json = os.path.join(self.output_dir, "patterns.json")
                self.output_dir_pattern = find_pattern(self.csv_file_notes, self.output_dir, self.part)
                self.pattern_analyzed = True
                # Adaugă toate fișierele din output_dir_pattern și subdirectoare
                for root, _, files in os.walk(self.output_dir_pattern):
                    for file in files:
                        if file.endswith((".json", ".png")):
                            self.generated_files["pattern"].add(os.path.relpath(os.path.join(root, file), self.output_dir))
                messagebox.showinfo("Success", "Pattern analysis completed.")
            except Exception as e:
                messagebox.showerror("Error", f"Pattern analysis failed: {e}")
        else:
            messagebox.showinfo("Info", "Pattern analysis already completed. Displaying existing results.")

        # Actualizează butoanele cu fișierele existente pentru analiza pattern-urilor
        self.scan_files(self.output_dir_pattern, "pattern")
        self.create_buttons()

    def scan_files(self, specific_dir=None, analysis_type=None):
        """Scanează fișierele din directorul specificat și le grupează pe tipuri de fișiere.

        Args:
            specific_dir (str): Directorul specificat pentru scanare. Dacă nu este specificat, se folosește output_dir.
            analysis_type (str): Tipul de analiză pentru a filtra fișierele (e.g., "notes", "segmentation").
        """

        self.files_by_folder = {}

        if specific_dir and os.path.isdir(specific_dir):
            root = specific_dir
        else:
            root = self.output_dir

        for root_dir, dirs, files in os.walk(root):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root_dir, file), self.output_dir)
                folder_path = os.path.dirname(rel_path)
                if folder_path not in self.files_by_folder:
                    self.files_by_folder[folder_path] = {"csv": [], "json": [], "png": [], "txt": []}

                if analysis_type:
                    # Filtrează doar fișierele asociate cu tipul de analiză specificat
                    if rel_path in self.generated_files.get(analysis_type, set()):
                        if file.endswith(".csv"):
                            self.files_by_folder[folder_path]["csv"].append(rel_path)
                        elif file.endswith(".png"):
                            self.files_by_folder[folder_path]["png"].append(rel_path)
                        elif file.endswith(".json"):
                            self.files_by_folder[folder_path]["json"].append(rel_path)
                        elif file.endswith(".txt"):
                            self.files_by_folder[folder_path]["txt"].append(rel_path)
                else:
                    # Dacă nu e specificat un tip de analiză, adaugă toate fișierele din director
                    if file.endswith(".csv"):
                        self.files_by_folder[folder_path]["csv"].append(rel_path)
                    elif file.endswith(".png"):
                        self.files_by_folder[folder_path]["png"].append(rel_path)
                    elif file.endswith(".json"):
                        self.files_by_folder[folder_path]["json"].append(rel_path)
                    elif file.endswith(".txt"):
                        self.files_by_folder[folder_path]["txt"].append(rel_path)

    def create_buttons(self):
        """
        Creează butoanele pentru fiecare folder și fișier găsit în directorul de ieșire.
        """
        # Șterge butoanele existente
        for widget in self.button_scrollable_frame.winfo_children():
            widget.destroy()

        # Adaugă buton pentru partitură
        if self.part:
            part_button = tk.Button(self.button_scrollable_frame, text="Show Partitura", command=self.show_partitura)
            part_button.pack(anchor="w", pady=5)

        # Creează butoane pentru fiecare folder
        for folder_path in sorted(self.files_by_folder.keys()):
            current_frame = self.button_scrollable_frame
            folder_parts = folder_path.split(os.sep) if folder_path else ["root"]
            for i, part in enumerate(folder_parts):
                frame_name = os.path.join(*folder_parts[:i+1])
                if not any(isinstance(child, tk.LabelFrame) and child.winfo_name() == frame_name for child in current_frame.winfo_children()):
                    folder_frame = tk.LabelFrame(current_frame, text=part, padx=5, pady=5, name=frame_name)
                    folder_frame.pack(side=tk.TOP, padx=5, pady=5, fill=tk.X)
                    current_frame = folder_frame
                else:
                    for child in current_frame.winfo_children():
                        if isinstance(child, tk.LabelFrame) and child.winfo_name() == frame_name:
                            current_frame = child
                            break

            folder_files = self.files_by_folder[folder_path]
            # CSV-PNG perechi
            if folder_files["csv"]:
                for csv_file in folder_files["csv"]:
                    csv_name = os.path.basename(csv_file)
                    button_csv = tk.Button(current_frame, text=f"Data: {csv_name}", command=lambda f=csv_file: self.show_content(f))
                    button_csv.pack(anchor="w", pady=2)
                    base_name = os.path.splitext(csv_file)[0]
                    png_associated = next((p for p in folder_files["png"] if base_name in p), None)
                    if png_associated:
                        png_name = os.path.basename(png_associated)
                        button_png = tk.Button(current_frame, text=f"Graph: {png_name}", command=lambda f=png_associated: self.show_content(f))
                        button_png.pack(anchor="w", pady=2)

            # JSON-PNG
            if folder_files["json"]:
                for json_file in folder_files["json"]:
                    json_name = os.path.basename(json_file)
                    button_json = tk.Button(current_frame, text=f"JSON: {json_name}", command=lambda f=json_file: self.show_content(f))
                    button_json.pack(anchor="w", pady=2)
                    base_name = os.path.splitext(json_file)[0]
                    png_associated = next((p for p in folder_files["png"] if base_name in p), None)
                    if png_associated:
                        png_name = os.path.basename(png_associated)
                        button_png = tk.Button(current_frame, text=f"Graph: {png_name}", command=lambda f=png_associated: self.show_content(f))
                        button_png.pack(anchor="w", pady=2)

            # TXT
            if folder_files["txt"]:
                for txt_file in folder_files["txt"]:
                    txt_name = os.path.basename(txt_file)
                    button_txt = tk.Button(current_frame, text=f"Text: {txt_name}", command=lambda f=txt_file: self.show_content(f))
                    button_txt.pack(anchor="w", pady=2)

            # PNG neasociate
            associated_pngs = {os.path.basename(p) for csv_file in folder_files["csv"] for p in folder_files["png"] if os.path.splitext(csv_file)[0] in p}
            associated_pngs.update({os.path.basename(p) for json_file in folder_files["json"] for p in folder_files["png"] if os.path.splitext(json_file)[0] in p})
            for png_file in folder_files["png"]:
                if os.path.basename(png_file) not in associated_pngs:
                    png_name = os.path.basename(png_file)
                    button_png = tk.Button(current_frame, text=f"Graph: {png_name}", command=lambda f=png_file: self.show_content(f))
                    button_png.pack(anchor="w", pady=2)

    def show_partitura(self):
        """
        Afișează partitura în MuseScore.
        """
        if self.part:
            try:
                # Salvează partitura ca MusicXML temporar
                musicxml_path = os.path.join(self.output_dir, "partitura_temp.xml")
                self.part.write('musicxml', fp=musicxml_path)

                # Deschide MuseScore cu fișierul MusicXML
                musescore_path = "/usr/bin/musescore"
                subprocess.run([musescore_path, musicxml_path])
            except Exception as e:
                messagebox.showerror("Error", f"Can't show partitura: {e}. Ensure MuseScore is installed and accessible at {musescore_path}.")

    def show_content(self, file_path):
        """
        Afișează conținutul fișierului selectat (CSV, JSON, PNG, TXT) în Treeview sau Label.
        """
        self.clear_display()
        full_path = os.path.join(self.output_dir, file_path)

        if file_path.endswith(".csv"):
            with open(full_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                headers = reader.fieldnames
                self.tree["columns"] = headers
                for header in headers:
                    self.tree.heading(header, text=header)
                for row in reader:
                    values = [row[header] for header in headers]
                    self.tree.insert("", tk.END, values=values)

            png_file = file_path.replace(".csv", ".png")
            png_path = os.path.join(self.output_dir, png_file)
            if os.path.exists(png_path):
                self.current_display_path = png_path
                self.display_content()
            else:
                self.display_label.pack_forget()

        elif file_path.endswith(".json"):
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if "patterns" in file_path:
                self.tree["columns"] = ("Pattern", "Start", "End")
                self.tree.heading("Pattern", text="Pattern")
                self.tree.heading("Start", text="Start (quarterLength)")
                self.tree.heading("End", text="End (quarterLength)")
                for pattern_entry in data:
                    pattern = pattern_entry['pattern']
                    source_voice = pattern['source_voice']
                    onset = pattern['onset']
                    num_notes = pattern['num_notes']
                    end = onset + num_notes - 1
                    segment_name = f"{source_voice}: {pattern['notes']}"
                    self.tree.insert("", tk.END, values=(segment_name, f"{onset:.3f}", f"{end:.3f}"))
            else:
                self.tree["columns"] = ("Key", "Value", "Details")
                self.tree.heading("Key", text="Key")
                self.tree.heading("Value", text="Value")
                self.tree.heading("Details", text="Details")
                for key, value in data.items():
                    details = ""
                    if isinstance(value, dict):
                        details = json.dumps(value, indent=2)[:50] + "..." if len(json.dumps(value)) > 50 else json.dumps(value)
                        value = "Dictionary"
                    elif isinstance(value, list):
                        details = json.dumps(value, indent=2)[:50] + "..." if len(json.dumps(value)) > 50 else json.dumps(value)
                        value = "List"
                    self.tree.insert("", tk.END, values=(key, value, details))

        elif file_path.endswith(".png"):
            self.current_display_path = full_path
            self.display_content()

        elif file_path.endswith(".txt"):
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                self.tree["columns"] = ("Line", "Value", "Details")
                self.tree.heading("Line", text="Line")
                self.tree.heading("Value", text="Value")
                self.tree.heading("Details", text="Details")
                for idx, line in enumerate(lines[:10], 1):
                    parts = line.strip().split(": ", 1) if ": " in line else (line.strip(), "")
                    value = parts[1] if len(parts) > 1 else ""
                    details = "" if len(parts) <= 1 else parts[0]
                    self.tree.insert("", tk.END, values=(f"Line {idx}", value, details))

    def display_content(self):
        """
        Afișează conținutul fișierului curent în display_label.
        """
        if not hasattr(self, 'current_display_path') or self.current_display_path is None:
            self.display_label.pack_forget()
            return

        frame_width = self.display_frame.winfo_width()
        frame_height = self.display_frame.winfo_height()

        try:
            img = Image.open(self.current_display_path)
            img.thumbnail((frame_width, frame_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.display_label.config(image=photo)
            self.display_label.image = photo
            self.display_label.pack(fill=tk.BOTH, expand=True)
            self.tree.pack_forget()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")
            self.display_label.pack_forget()

    def resize_display(self, event):
        """
        Redimensionează afișarea conținutului în funcție de dimensiunea frame-ului.
        """

        if hasattr(self, 'current_display_path') and self.current_display_path is not None and self.current_display_path.endswith(".png"):
            self.display_content()

    def clear_display(self):
        """
        Curăță afișarea curentă și resetează Treeview-ul.
        """
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree["columns"] = ("Field1", "Field2", "Field3")
        self.tree.heading("Field1", text="Field1")
        self.tree.heading("Field2", text="Field2")
        self.tree.heading("Field3", text="Field3")
        self.display_label.pack_forget()
        self.tree.pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()