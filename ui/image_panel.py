import tkinter as tk
import threading
from pathlib import Path
import re
import queue

from PIL import Image, ImageTk

class StaticMudraImageWindow:
    """Separate Tkinter window showing up to four dataset images per mudra."""

    def __init__(self, parent, dataset_path=None):
        self.parent = parent
        project_root = Path(__file__).resolve().parent.parent
        self.dataset_path = Path(dataset_path) if dataset_path else project_root / "dataset"
        self.window = None
        self.current_mudra = None
        self.photo_references = []

    @staticmethod
    def _normalise(value):
        value = re.sub(r"\s*\(\d+\)$", "", str(value))
        return re.sub(r"[^a-z0-9]", "", value.lower())

    def _find_folder(self, mudra_name):
        if not self.dataset_path.is_dir():
            return None
        wanted = self._normalise(mudra_name)
        folders = [p for p in self.dataset_path.iterdir() if p.is_dir()]
        # Prefer exact normalized directory-name matches.
        for folder in folders:
            if self._normalise(folder.name) == wanted:
                return folder
        # Allow canonical aliases used by the existing text recognizer.
        aliases = self._aliases_for(mudra_name)
        alias_keys = {self._normalise(a) for a in aliases}
        for folder in folders:
            if self._normalise(folder.name) in alias_keys:
                return folder
        return None

    def _aliases_for(self, mudra_name):
        key = self._normalise(mudra_name)
        for canonical, aliases in self._mudra_aliases().items():
            if self._normalise(canonical) == key:
                return [canonical, *aliases]
            if any(self._normalise(alias) == key for alias in aliases):
                return [canonical, *aliases]
        return [mudra_name]

    @staticmethod
    def _sort_key(path):
        match = re.search(r"_(\d+)$", path.stem)
        return (0, int(match.group(1))) if match else (1, path.name.lower())

    def show_mudra(self, mudra_name):
        if not mudra_name:
            return
        folder = self._find_folder(mudra_name)
        if folder is None:
            self._show_message(
                mudra_name,
                f"Dataset folder not found for '{mudra_name}'.\n\n"
                f"Expected a matching folder inside:\n{self.dataset_path}"
            )
            return

        images = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
        images.sort(key=self._sort_key)
        self._ensure_window()
        self.current_mudra = mudra_name
        self.title_label.configure(text=f"{mudra_name.replace('_', ' ')} — Reference Images")
        for child in self.grid_frame.winfo_children():
            child.destroy()
        self.photo_references.clear()

        if not images:
            self._show_message(mudra_name, f"No JPG/PNG images found in:\n{folder}")
            return

        for index, image_path in enumerate(images[:4]):
            try:
                with Image.open(image_path) as source:
                    image = source.convert("RGB")
                    image.thumbnail((330, 290))
                photo = ImageTk.PhotoImage(image, master=self.window)
                self.photo_references.append(photo)
                card = tk.Frame(self.grid_frame, bg="#F2F5F6", padx=8, pady=8)
                card.grid(row=index // 2, column=index % 2, padx=10, pady=10, sticky="nsew")
                tk.Label(card, image=photo, bg="#F2F5F6").pack(expand=True)
                tk.Label(card, text=image_path.name, bg="#F2F5F6", fg="#172B36",
                         font=("Segoe UI", 9, "bold")).pack(pady=(6, 0))
            except Exception as exc:
                tk.Label(self.grid_frame, text=f"Could not load {image_path.name}: {exc}",
                         bg="#FFFFFF", fg="#A93226", wraplength=300).grid(
                             row=index // 2, column=index % 2, padx=10, pady=10)

        self.window.deiconify()
        self.window.lift()

    def _ensure_window(self):
        if self.window is not None and self.window.winfo_exists():
            return
        self.window = tk.Toplevel(self.parent)
        self.window.title("Bharatanatyam — Mudra Reference Images")
        self.window.geometry("760x760")
        self.window.minsize(600, 560)
        self.window.configure(bg="#FFFFFF")
        self.window.protocol("WM_DELETE_WINDOW", self.window.withdraw)
        self.title_label = tk.Label(self.window, text="Mudra Reference Images",
                                    font=("Segoe UI", 15, "bold"),
                                    bg="#FFFFFF", fg="#172B36")
        self.title_label.pack(anchor="w", padx=18, pady=(16, 8))
        self.grid_frame = tk.Frame(self.window, bg="#FFFFFF")
        self.grid_frame.pack(fill="both", expand=True, padx=12, pady=8)
        self.grid_frame.grid_columnconfigure(0, weight=1)
        self.grid_frame.grid_columnconfigure(1, weight=1)
        self.grid_frame.grid_rowconfigure(0, weight=1)
        self.grid_frame.grid_rowconfigure(1, weight=1)

    def _show_message(self, mudra_name, message):
        self._ensure_window()
        self.current_mudra = mudra_name
        self.title_label.configure(text=f"{mudra_name.replace('_', ' ')} — Reference Images")
        for child in self.grid_frame.winfo_children():
            child.destroy()
        self.photo_references.clear()
        tk.Label(self.grid_frame, text=message, bg="#FFFFFF", fg="#687B85",
                 font=("Segoe UI", 11), justify="center", wraplength=600).pack(
                     expand=True, padx=20, pady=20)
        self.window.deiconify()
        self.window.lift()

    def clear(self, close_window=False):
        self.current_mudra = None
        self.photo_references.clear()
        if self.window is not None and self.window.winfo_exists():
            if close_window:
                self.window.destroy()
                self.window = None
            else:
                self.window.withdraw()

    @staticmethod
    def get_mudra_from_question(question):
        """
        Identify a mudra from the question without checking
        mudra_library or any image folders.
        """


        supported_mudras = {
            # 1–6
            "sikharam": ["sikharam", "shikharam", "shikhara"],
            "simhamukham": ["simhamukham", "simhamukha", "simha mukha"],
            "suchi": ["suchi", "suchi mudra"],
            "tamarachudam": ["tamarachudam", "tamrachudam", "tamrachuda"],
            "tripathaka": ["tripathaka", "tripataka", "tri pataka"],
            "trishulam": ["trishulam", "trishula", "trishul"],

            # 7–27
            "katakavardhana": ["katakavardhana", "kataka vardhana"],
            "katrimukha": ["katrimukha", "katri mukha"],
            "khatva": ["khatva", "khatva mudra"],
            "kilaka": ["kilaka"],
            "kurma": ["kurma", "kurma mudra"],
            "matsya": ["matsya", "matsya mudra"],
            "mayura": ["mayura", "mayur"],
            "mrigasirsha": ["mrigasirsha", "mrigashirsha", "mriga shirsha"],
            "mukulam": ["mukulam", "mukula"],
            "mushti": ["mushti", "musthi", "mushti mudra"],
            "nagabandha": ["nagabandha", "naga bandha"],
            "padmakosha": ["padmakosha", "padma kosha"],
            "pasha": ["pasha", "pasa"],
            "pathaka": ["pathaka", "pataka"],
            "pushpaputa": ["pushpaputa", "pushpa puta"],
            "sakata": ["sakata", "shakata"],
            "samputa": ["samputa"],
            "sarpasirsha": ["sarpasirsha", "sarpashirsha", "sarpa shirsha"],
            "shanka": ["shanka", "shankha"],
            "shivalinga": ["shivalinga", "shiva linga"],
            "shukathundam": ["shukathundam", "shukatunda", "shuka tunda"],

            # 28–48
            "alapadmam": ["alapadmam", "alapadma", "alapadma hasta"],
            "anjali": ["anjali", "anjali mudra"],
            "aralam": ["aralam", "arala"],
            "ardhachandran": ["ardhachandran", "ardhachandra", "ardha chandra"],
            "ardhapathaka": ["ardhapathaka", "ardhapataka", "ardha pataka"],
            "berunda": ["berunda", "bherunda"],
            "bramaram": ["bramaram", "bhramaram", "bhramara"],
            "chakra": ["chakra", "chakra mudra"],
            "chandrakala": ["chandrakala", "chandra kala"],
            "chaturam": ["chaturam", "chatura"],
            "garuda": ["garuda", "garuda mudra"],
            "hamsapaksha": ["hamsapaksha", "hamsa paksha"],
            "hamsasyam": ["hamsasyam", "hamsasya", "hamsa asya"],
            "kangulam": ["kangulam", "kangula"],
            "kapith": ["kapith", "kapittha", "kapitta"],
            "kapotham": ["kapotham", "kapota", "kapotha"],
            "karkatta": ["karkatta", "karkata"],
            "kartariswastika": [
                "kartariswastika",
                "kartari swastika",
                "kartari svastika"
            ],
            "katakamukha_1": ["katakamukha 1", "katakamukha_1"],
            "katakamukha_2": ["katakamukha 2", "katakamukha_2"],
            "katakamukha_3": ["katakamukha 3", "katakamukha_3"],

            # 49
            "varaha": ["varaha", "varaha mudra"]
        }


        question = question.lower()

        # Check longer names first to avoid partial matches.
        aliases = []

        for canonical_name, variations in supported_mudras.items():
            for variation in variations:
                aliases.append((variation, canonical_name))

        aliases.sort(key=lambda item: len(item[0]), reverse=True)

        for alias, canonical_name in aliases:

            pattern = (
                r"(?<![a-z])"
                + re.escape(alias)
                + r"(?![a-z])"
            )

            if re.search(pattern, question):
                return canonical_name

        return None


    @staticmethod
    def _mudra_aliases():
        return {
            "sikharam": ["sikharam", "shikharam", "shikhara"],
            "simhamukham": ["simhamukham", "simhamukha", "simha mukha"],
            "suchi": ["suchi", "suchi mudra"],
            "tamarachudam": ["tamarachudam", "tamrachudam", "tamrachuda"],
            "tripathaka": ["tripathaka", "tripataka", "tri pataka"],
            "trishulam": ["trishulam", "trishula", "trishul"],
            "katakavardhana": ["katakavardhana", "kataka vardhana"],
            "katrimukha": ["katrimukha", "katri mukha"],
            "khatva": ["khatva", "khatva mudra"], "kilaka": ["kilaka"],
            "kurma": ["kurma", "kurma mudra"], "matsya": ["matsya", "matsya mudra"],
            "mayura": ["mayura", "mayur"], "mrigasirsha": ["mrigasirsha", "mrigashirsha", "mriga shirsha"],
            "mukulam": ["mukulam", "mukula"], "mushti": ["mushti", "musthi", "mushti mudra"],
            "nagabandha": ["nagabandha", "naga bandha"], "padmakosha": ["padmakosha", "padma kosha"],
            "pasha": ["pasha", "pasa"], "pathaka": ["pathaka", "pataka"],
            "pushpaputa": ["pushpaputa", "pushpa puta"], "sakata": ["sakata", "shakata"],
            "samputa": ["samputa"], "sarpasirsha": ["sarpasirsha", "sarpashirsha", "sarpa shirsha"],
            "shanka": ["shanka", "shankha"], "shivalinga": ["shivalinga", "shiva linga"],
            "shukathundam": ["shukathundam", "shukatunda", "shuka tunda"],
            "alapadmam": ["alapadmam", "alapadma", "alapadma hasta"], "anjali": ["anjali", "anjali mudra"],
            "aralam": ["aralam", "arala"], "ardhachandran": ["ardhachandran", "ardhachandra", "ardha chandra"],
            "ardhapathaka": ["ardhapathaka", "ardhapataka", "ardha pataka"], "berunda": ["berunda", "bherunda"],
            "bramaram": ["bramaram", "bhramaram", "bhramara"], "chakra": ["chakra", "chakra mudra"],
            "chandrakala": ["chandrakala", "chandra kala"], "chaturam": ["chaturam", "chatura"],
            "garuda": ["garuda", "garuda mudra"], "hamsapaksha": ["hamsapaksha", "hamsa paksha"],
            "hamsasyam": ["hamsasyam", "hamsasya", "hamsa asya"], "kangulam": ["kangulam", "kangula"],
            "kapith": ["kapith", "kapittha", "kapitta"], "kapotham": ["kapotham", "kapota", "kapotha"],
            "karkatta": ["karkatta", "karkata"],
            "kartariswastika": ["kartariswastika", "kartari swastika", "kartari svastika"],
            "katakamukha_1": ["katakamukha 1", "katakamukha_1"],
            "katakamukha_2": ["katakamukha 2", "katakamukha_2"],
            "katakamukha_3": ["katakamukha 3", "katakamukha_3"],
            "varaha": ["varaha", "varaha mudra"],
        }


class MudraImageSelectionController:
    """
    Controls image selection between text and camera.

    All Tkinter image-window operations are executed
    on the Tkinter main thread.
    """

    def __init__(self, image_window):
        self.image_window = image_window

        self.lock = threading.RLock()
        self.update_queue = queue.Queue()

        self.selected_mudra = None
        self.selection_source = None

        self.text_priority = False
        self.camera_active = False

        self.closed = False

        self.selection_version = 0

        # Process image updates on the Tkinter main thread.
        self.image_window.parent.after(
            50,
            self._process_updates
        )
    def _queue_update(self, action, mudra=None):

        self.selection_version += 1

        self.update_queue.put(
            (
                action,
                mudra,
                self.selection_version
            )
        )

    def _process_updates(self):

        try:
            while True:

                action, mudra, version = (
                    self.update_queue.get_nowait()
                )

                # Always process close, even if the controller
                # has already been marked as closed.
                if action == "close":
                    self.image_window.clear(
                        close_window=True
                    )
                    return

                with self.lock:

                    # Ignore outdated image requests.
                    if version != self.selection_version:
                        continue

                    if self.closed:
                        return

                if action == "show":
                    self.image_window.show_mudra(mudra)

                elif action == "clear":
                    self.image_window.clear(
                        close_window=False
                    )

        except queue.Empty:
            pass

        # Do not schedule another callback after closing.
        if not self.closed:
            self.image_window.parent.after(
                50,
                self._process_updates
            )


    def select_text_mudra(self, mudra_name):
        if not mudra_name:
            return False

        with self.lock:
            if self.closed:
                return False

            self.selected_mudra = mudra_name
            self.selection_source = "text"

            if self.camera_active:
                self.text_priority = True

            self._queue_update("show", mudra_name)

        return True


    def select_camera_mudra(self, mudra_name):
        if not mudra_name:
            return False

        with self.lock:
            if self.closed or not self.camera_active:
                return False

            # Allow a new camera prediction to replace
            # the previously text-selected mudra.
            if self.selected_mudra == mudra_name:
                return False

            self.selected_mudra = mudra_name
            self.selection_source = "camera"
            self.text_priority = False

            self._queue_update("show", mudra_name)

        return True


    def start_camera(self):
        with self.lock:
            if self.closed:
                return

            self.camera_active = True
            self.text_priority = False

    def stop_camera(self, teaching_mudra=None):
        with self.lock:
            if self.closed:
                return

            self.camera_active = False
            self.text_priority = False

            if teaching_mudra:
                self.selected_mudra = teaching_mudra
                self.selection_source = "text"

                self._queue_update(
                    "show",
                    teaching_mudra
                )

            else:
                self.selected_mudra = None
                self.selection_source = None

                self._queue_update("clear")

    def clear(self):
        with self.lock:
            if self.closed:
                return

            self.camera_active = False
            self.text_priority = False
            self.selected_mudra = None
            self.selection_source = None

            self._queue_update("clear")


    def close(self):

        with self.lock:

            if self.closed:
                return

            self.closed = True

            self.camera_active = False
            self.text_priority = False

            self.selected_mudra = None
            self.selection_source = None

            self.selection_version += 1

            # Queue the close operation for the Tkinter main thread.
            self.update_queue.put(
                (
                    "close",
                    None,
                    self.selection_version
                )
            )

