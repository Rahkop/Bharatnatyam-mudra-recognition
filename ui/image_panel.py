
import os
import tkinter as tk
from tkinter import ttk
import re

from PIL import Image, ImageTk


class MudraImagePanel:
    """
    Displays reference images for the mudra currently
    being taught by the AI tutor.
    """

    def __init__(self, parent, library_path="mudra_library"):

        self.parent = parent
        self.library_path = library_path

        self.current_mudra = None
        self.photo_references = []

        self.frame = tk.Frame(
            parent,
            bg="#FFFFFF",
            width=270
        )

        self.frame.pack_propagate(False)

        self.title_label = tk.Label(
            self.frame,
            text="Mudra References",
            font=("Segoe UI", 13, "bold"),
            bg="#FFFFFF",
            fg="#172B36"
        )
        self.title_label.pack(
            anchor="w",
            padx=12,
            pady=(12, 5)
        )

        self.mudra_label = tk.Label(
            self.frame,
            text="No mudra selected",
            font=("Segoe UI", 10, "bold"),
            bg="#FFFFFF",
            fg="#16A085"
        )
        self.mudra_label.pack(
            anchor="w",
            padx=12,
            pady=(0, 10)
        )

        self.image_container = tk.Frame(
            self.frame,
            bg="#FFFFFF"
        )
        self.image_container.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5
        )

        self.message_label = tk.Label(
            self.image_container,
            text=(
                "Ask your tutor to teach a mudra.\n\n"
                "Its reference images will appear here."
            ),
            font=("Segoe UI", 10),
            bg="#FFFFFF",
            fg="#687B85",
            wraplength=220,
            justify="center"
        )
        self.message_label.pack(
            expand=True
        )


    def get_mudra_from_question(self, question):
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


    def set_mudra(
        self,
        mudra_name,
        generated_image_path=None,
        status_message=None
    ):

        if not mudra_name:
            return

        for widget in self.image_container.winfo_children():
            widget.destroy()

        self.photo_references.clear()

        self.current_mudra = mudra_name

        self.mudra_label.configure(
            text=mudra_name.replace("_", " ")
        )

        # Display the generated image.
        if (
            generated_image_path
            and os.path.isfile(generated_image_path)
        ):

            try:
                self._display_image(
                    generated_image_path,
                    "AI-generated mudra illustration"
                )

                warning = tk.Label(
                    self.image_container,
                    text=(
                        "AI-generated illustration. "
                        "Verify traditional hand positions "
                        "with an authentic reference."
                    ),
                    font=("Segoe UI", 8),
                    bg="#FFFFFF",
                    fg="#A93226",
                    wraplength=220,
                    justify="center"
                )

                warning.pack(pady=5)

                return

            except Exception as exc:
                print("Generated image display error:", exc)

        # Display loading or error message.
        message = status_message or (
            "No generated image available."
        )

        self.message_label = tk.Label(
            self.image_container,
            text=message,
            font=("Segoe UI", 10),
            bg="#FFFFFF",
            fg="#687B85",
            wraplength=220,
            justify="center"
        )

        self.message_label.pack(expand=True)
        

    def _display_image(self, image_path, title):

        image = Image.open(image_path).convert("RGB")
        image.thumbnail((225, 300))

        photo = ImageTk.PhotoImage(image)

        self.photo_references.append(photo)

        card = tk.Frame(
            self.image_container,
            bg="#F2F5F6",
            padx=5,
            pady=5
        )

        card.pack(
            fill="x",
            pady=5
        )

        label = tk.Label(
            card,
            image=photo,
            bg="#F2F5F6"
        )

        label.pack()

        caption = tk.Label(
            card,
            text=title,
            font=("Segoe UI", 9, "bold"),
            bg="#F2F5F6",
            fg="#172B36"
        )

        caption.pack(pady=(4, 2))


    def clear(self):
        """Clear the previous mudra's reference images."""

        for widget in self.image_container.winfo_children():
            widget.destroy()

        self.photo_references.clear()
        self.current_mudra = None

        self.mudra_label.configure(
            text="No mudra selected"
        )

        self.message_label = tk.Label(
            self.image_container,
            text="Ask your tutor to teach a mudra.",
            font=("Segoe UI", 10),
            bg="#FFFFFF",
            fg="#687B85"
        )

        self.message_label.pack(expand=True)


    def pack(self, **kwargs):
        """Allow the panel to be packed like a Tkinter widget."""

        self.frame.pack(**kwargs)


    def pack_forget(self):
        """Hide the panel without destroying it."""

        self.frame.pack_forget()

