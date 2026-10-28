
import queue
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

from ai.mudra_tutor import MudraTutor


class MudraTutorChat:
    """Desktop chat interface for the unified Bharatanatyam tutor."""

    def __init__(
        self,
        root,
        tutor=None,
        context_provider=None,
        on_close=None,
    ):
        self.root = root
        self.tutor = tutor
        self.context_provider = context_provider
        self.on_close_callback = on_close
        self.messages = queue.Queue()
        self.busy = False
        self.closed = False

        self.root.title("Bharatanatyam AI Mudra Tutor")
        self.root.geometry("760x520")
        self.root.minsize(560, 400)
        self.root.configure(bg="#10232F")

        self._build_interface()
        self._show_message(
            "Tutor",
            "Namaste! I'm your Bharatanatyam AI Tutor.\n\n"
            "Ask me about mudras, their meanings, dance terminology, "
            "practice techniques, or general Bharatanatyam topics.\n\n"
            "You can also ask follow-up questions in this conversation."
        )

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(100, self._process_messages)

        # Initialize the API client outside the GUI thread.
        if self.tutor is None:
            self._set_status("Connecting to Gemini...")
            threading.Thread(
                target=self._initialize_tutor,
                daemon=True,
            ).start()
        else:
            self._set_status("Ready")

    def _build_interface(self):
        header = tk.Frame(self.root, bg="#10232F")
        header.pack(fill="x", padx=18, pady=(16, 10))

        title = tk.Label(
            header,
            text="Bharatanatyam AI Tutor",
            font=("Segoe UI", 18, "bold"),
            fg="#F2F6F8",
            bg="#10232F",
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            header,
            text="Learn mudras • Explore meanings • Practice with guidance",
            font=("Segoe UI", 10),
            fg="#A9C0CD",
            bg="#10232F",
        )
        subtitle.pack(anchor="w", pady=(4, 0))

        self.chat_area = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Segoe UI", 11),
            bg="#F5F7F8",
            fg="#172B36",
            padx=14,
            pady=12,
            relief=tk.FLAT,
            borderwidth=0,
            height=12,
        )
        self.chat_area.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=(0, 12),
        )

        self.chat_area.tag_configure(
            "speaker",
            font=("Segoe UI", 10, "bold"),
            spacing1=8,
            spacing3=3,
        )
        self.chat_area.tag_configure(
            "user",
            foreground="#176B87",
        )
        self.chat_area.tag_configure(
            "tutor",
            foreground="#7652A3",
        )
        self.chat_area.tag_configure(
            "body",
            font=("Segoe UI", 10),
            spacing3=8,
        )

        self.status_label = tk.Label(
            self.root,
            text="Starting...",
            anchor="w",
            font=("Segoe UI", 9),
            fg="#B7CDD6",
            bg="#10232F",
        )
        self.status_label.pack(fill="x", padx=20, pady=(0, 8))

        input_frame = tk.Frame(self.root, bg="#10232F")
        input_frame.pack(fill="x", padx=18, pady=(0, 16))

        self.input_box = tk.Text(
            input_frame,
            height=3,
            wrap=tk.WORD,
            font=("Segoe UI", 11),
            bg="#FFFFFF",
            fg="#172B36",
            insertbackground="#172B36",
            relief=tk.FLAT,
            padx=10,
            pady=8,
        )
        self.input_box.pack(
            side="left",
            fill="both",
            expand=True,
        )
        self.input_box.bind("<Control-Return>", self._send_message)

        self.send_button = tk.Button(
            input_frame,
            text="Send",
            command=self._send_message,
            font=("Segoe UI", 10, "bold"),
            bg="#16A085",
            fg="#FFFFFF",
            activebackground="#12816B",
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            padx=18,
            pady=10,
            cursor="hand2",
        )
        self.send_button.pack(
            side="left",
            padx=(10, 0),
            anchor="s",
        )

        self.clear_button = tk.Button(
            self.root,
            text="New conversation",
            command=self._clear_conversation,
            font=("Segoe UI", 9),
            bg="#10232F",
            fg="#A9C0CD",
            activebackground="#10232F",
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            cursor="hand2",
        )
        self.clear_button.pack(anchor="e", padx=18, pady=(0, 8))

    def _show_message(self, speaker, text):
        self.chat_area.configure(state=tk.NORMAL)

        tag = "user" if speaker == "You" else "tutor"

        self.chat_area.insert(
            tk.END,
            f"{speaker}\n",
            ("speaker", tag),
        )
        self.chat_area.insert(
            tk.END,
            f"{text}\n\n",
            ("body",),
        )

        self.chat_area.configure(state=tk.DISABLED)
        self.chat_area.see(tk.END)

    def _set_status(self, text):
        self.status_label.configure(text=text)

    def _initialize_tutor(self):
        try:
            tutor = MudraTutor()
            self.messages.put(("initialized", tutor))
        except Exception as exc:
            self.messages.put(("initialization_error", str(exc)))

    def _send_message(self, event=None):
        if self.closed:
            return "break"

        question = self.input_box.get("1.0", tk.END).strip()

        if not question:
            return "break"

        if self.busy:
            self._set_status("Please wait for the current response.")
            return "break"

        if self.tutor is None:
            self._set_status("Gemini is not ready yet.")
            return "break"

        self.input_box.delete("1.0", tk.END)
        self._show_message("You", question)

        self.busy = True
        self.send_button.configure(state=tk.DISABLED)
        self._set_status("Thinking...")

        threading.Thread(
            target=self._ask_tutor,
            args=(question,),
            daemon=True,
        ).start()

        return "break"

    def _ask_tutor(self, question):
        try:
            context = {}

            if self.context_provider is not None:
                context = self.context_provider() or {}

            answer = self.tutor.ask(
                question,
                current_mudra=context.get("mudra"),
                confidence=context.get("confidence"),
            )

            self.messages.put(("answer", answer))

        except Exception as exc:
            self.messages.put(("error", str(exc)))

    def _process_messages(self):
        if self.closed:
            return

        try:
            while True:
                kind, payload = self.messages.get_nowait()

                if kind == "initialized":
                    self.tutor = payload
                    self._set_status("Ready")

                elif kind == "initialization_error":
                    self._set_status("Could not initialize Gemini.")
                    messagebox.showerror(
                        "Tutor initialization failed",
                        payload,
                    )

                elif kind == "answer":
                    self._show_message("Tutor", payload)
                    self.busy = False
                    self.send_button.configure(state=tk.NORMAL)
                    self._set_status("Ready")

                elif kind == "error":
                    self._show_message(
                        "Tutor",
                        "Sorry, I couldn't complete that request. "
                        "Please try again.\n\nDetails: " + payload,
                    )
                    self.busy = False
                    self.send_button.configure(state=tk.NORMAL)
                    self._set_status("Request failed")

        except queue.Empty:
            pass

        self.root.after(100, self._process_messages)

    def _clear_conversation(self):
        if self.busy:
            self._set_status(
                "Wait for the current response before starting a new conversation."
            )
            return

        if self.tutor is not None:
            self.tutor.reset_conversation()

        self.chat_area.configure(state=tk.NORMAL)
        self.chat_area.delete("1.0", tk.END)
        self.chat_area.configure(state=tk.DISABLED)

        self._show_message(
            "Tutor",
            "Namaste! A new conversation has started. "
            "What would you like to learn?",
        )
        self._set_status("Ready")

    def _on_close(self):
        self.closed = True

        if self.on_close_callback is not None:
            self.on_close_callback()

        if self.tutor is not None:
            threading.Thread(
                target=self.tutor.close,
                daemon=True,
            ).start()

        self.root.destroy()


def main():
    root = tk.Tk()
    MudraTutorChat(root)
    root.mainloop()


if __name__ == "__main__":
    main()
