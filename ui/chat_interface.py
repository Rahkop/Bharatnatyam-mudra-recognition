
import queue
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

from ai.mudra_tutor import MudraTutor
from ui.image_panel import MudraImagePanel
from ai.image_generator import CloudflareImageGenerator

class MudraTutorChat:
    """Desktop chat interface for the unified Bharatanatyam tutor."""

    def __init__(
        self,
        root,
        tutor=None,
        context_provider=None,
        on_close=None,
        on_camera_start=None,
        on_camera_stop=None,
    ):
        self.root = root
        self.tutor = tutor
        self.context_provider = context_provider
        self.on_close_callback = on_close
        self.on_camera_start = on_camera_start
        self.on_camera_stop = on_camera_stop
        self.messages = queue.Queue()
        self.busy = False
        self.closed = False
        # Track mudras currently being generated.
        self.image_generation_in_progress = set()

        # Store dynamically generated image paths.
        self.generated_image_cache = {}


        # Teaching context
        self.current_teaching_mudra = None

        # Intended mudra the learner wants to practise
        self.practice_target_mudra = None

        # Actual mudra detected by the camera
        self.detected_mudra = None

        # Image panel ownership
        self.image_display_context = None

        # Camera state
        self.camera_active = False

        # Learner's selected teaching level.
        self.learning_level = None


        # Phase 6: Stable prediction tracking
        self.candidate_mudra = None
        self.candidate_count = 0


        self.stable_mudra = None
        self.confidence_threshold = 0.70
        self.required_stable_samples = 4

        # Automatic feedback control
        self.auto_feedback_busy = False
        self.pending_practice_mudra = None

        self.root.title("Bharatanatyam AI Mudra Tutor")
        self.root.geometry("1050x760")
        self.root.minsize(900, 650)
        self.root.configure(bg="#10232F")

        self._build_interface()
        self._show_message(
            "Tutor",
            "Namaste! Welcome to your Bharatanatyam AI Tutor! 🙏\n\n"
            "I'm here to guide you through learning Bharatanatyam "
            "mudras, understanding their meanings, and practising "
            "their formations.\n\n"
            "Before we begin, please select your preferred "
            "learning level using the options above."
        )

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(100, self._process_messages)
        self.root.after(300, self._refresh_recognition_status)

        # Initialize the API client outside the GUI thread.
        if self.tutor is None:
            self._set_status("Connecting to Gemini...")
            threading.Thread(
                target=self._initialize_tutor,
                daemon=True,
            ).start()
        else:
            self._set_status("Ready")

    def hide_mudra_images(self):
        # Remove previous images
        self.image_panel.clear()

        # Hide the entire image panel
        self.image_panel.pack_forget()

        # Reset the current mudra
        self.current_teaching_mudra = None



    def _generate_mudra_image(self, mudra_name):

        try:

            generator = CloudflareImageGenerator()

            image_path = generator.generate_image(
                mudra_name
            )

            self.messages.put(
                (
                    "image_generated",
                    (mudra_name, image_path)
                )
            )

        except Exception as exc:

            self.messages.put(
                (
                    "image_generation_error",
                    (mudra_name, str(exc))
                )
            )




    def _request_mudra_image(self, mudra_name):

        if not mudra_name:
            return

        # Display the image panel.
        self.image_panel.pack(
            side="right",
            fill="y",
            padx=(5, 0)
        )

        # Check whether this image was already generated.
        cached_image = self.generated_image_cache.get(
            mudra_name
        )

        if cached_image:
            import os

            if os.path.isfile(cached_image):

                self.image_panel.set_mudra(
                    mudra_name,
                    generated_image_path=cached_image
                )

                return

        # Display loading message if image is not cached.
        self.image_panel.set_mudra(
            mudra_name,
            status_message=(
                "Generating your mudra illustration...\n\n"
                "Please wait."
            )
        )

        # Avoid duplicate simultaneous requests.
        if mudra_name in self.image_generation_in_progress:
            return

        self.image_generation_in_progress.add(mudra_name)

        # Generate image in background thread.
        threading.Thread(
            target=self._generate_mudra_image,
            args=(mudra_name,),
            daemon=True
        ).start()



    def show_mudra_images(self, mudra_name):
        """
        Update teaching context.

        Teaching can update while the camera is active,
        but it must not replace the practice image.
        """

        if not mudra_name:
            return

        self.current_teaching_mudra = mudra_name

        # Practice owns the panel while the camera is active.
        if self.camera_active:
            return

        self.image_display_context = "teaching"

        self._request_mudra_image(mudra_name)

    def show_practice_mudra_images(self, mudra_name):
        """
        Display the currently detected practice mudra.
        """

        if not mudra_name:
            return

        self.detected_mudra = mudra_name

        # Practice images should only appear during camera practice.
        if not self.camera_active:
            return

        self.image_display_context = "practice"

        self._request_mudra_image(mudra_name)
        
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

        # Learning level selection
        self.level_frame = tk.Frame(
            self.root,
            bg="#10232F"
        )
        self.level_frame.pack(fill="x", padx=18, pady=(12, 10))

        level_label = tk.Label(
            self.level_frame,
            text="How would you like your tutor to teach you?",
            font=("Segoe UI", 11, "bold"),
            fg="#F2F6F8",
            bg="#10232F"
        )
        level_label.pack(anchor="w", pady=(0, 8))

        button_frame = tk.Frame(
            self.level_frame,
            bg="#10232F"
        )
        button_frame.pack(anchor="w")

        self.beginner_button = tk.Button(
            button_frame,
            text="Beginner Friendly",
            command=lambda: self._select_learning_level("beginner"),
            font=("Segoe UI", 10, "bold"),
            bg="#16A085",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2"
        )
        self.beginner_button.pack(side="left", padx=(0, 10))

        self.intermediate_button = tk.Button(
            button_frame,
            text="Intermediate",
            command=lambda: self._select_learning_level("intermediate"),
            font=("Segoe UI", 10, "bold"),
            bg="#2874A6",
            fg="white",
            relief=tk.FLAT,
            padx=15,
            pady=8,
            cursor="hand2"
        )
        self.intermediate_button.pack(side="left")

        self.content_frame = tk.Frame(
            self.root,
            bg="#10232F"
        )

        self.content_frame.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=(0, 12)
        )

        self.chat_area = scrolledtext.ScrolledText(
            self.content_frame,
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
            side="left",
            fill="both",
            expand=True,
            padx=(0, 10),
        )

        # Mudra reference image panel
        self.image_panel = MudraImagePanel(
            self.content_frame,
            library_path="mudra_library"
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

        self.recognition_label = tk.Label(
            self.root,
            text="Camera: Off",
            anchor="w",
            font=("Segoe UI", 9, "bold"),
            fg="#A9C0CD",
            bg="#10232F",
        )

        self.recognition_label.pack(
            fill="x",
            padx=20,
            pady=(0, 8)
        )

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

        self.camera_start_button = tk.Button(
            input_frame,
            text="Start Camera Practice",
            command=self._start_camera,
            font=("Segoe UI", 9, "bold"),
            bg="#2874A6",
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=10,
            cursor="hand2"
        )

        self.camera_start_button.pack(
            side="left",
            padx=(10, 0),
            anchor="s"
        )

        self.camera_stop_button = tk.Button(
            input_frame,
            text="Stop Camera",
            command=self._stop_camera,
            font=("Segoe UI", 9, "bold"),
            bg="#A93226",
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=10,
            cursor="hand2",
            state=tk.DISABLED
        )

        self.camera_stop_button.pack(
            side="left",
            padx=(5, 0),
            anchor="s"
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


    def _select_learning_level(self, level):

        self.learning_level = level

        if level == "beginner":
            message = (
                "You selected Beginner Friendly mode.\n\n"
                "I'll explain each mudra in detail, including "
                "finger positioning, hand orientation, meanings, "
                "and step-by-step practice instructions."
            )
        else:
            message = (
                "You selected Intermediate mode.\n\n"
                "I'll provide concise explanations, essential "
                "mudra formations, and focused practice corrections."
            )

        self._show_message("Tutor", message)

        # Disable level selection after choosing
        self.beginner_button.configure(state=tk.DISABLED)
        self.intermediate_button.configure(state=tk.DISABLED)

        self._set_status(
            f"Learning mode: {level.capitalize()}"
        )



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

        if self.learning_level is None:
            messagebox.showinfo(
                "Select Learning Level",
                "Please select Beginner Friendly or Intermediate "
                "before starting your learning session."
            )
            return "break"


        if self.busy or self.auto_feedback_busy:
            self._set_status("Please wait for the current response.")
            return "break"

        if self.tutor is None:
            self._set_status("Gemini is not ready yet.")
            return "break"



    # Identify whether the learner requested a new teaching mudra.
        requested_mudra = self.image_panel.get_mudra_from_question(
            question
        )

        if requested_mudra:

            # Update the teaching topic.
            self.show_mudra_images(requested_mudra)

        elif self.current_teaching_mudra:

            # Follow-up question.
            # Update teaching context without taking over
            # the image panel during active camera practice.
            self.show_mudra_images(
                self.current_teaching_mudra
            )




        self.input_box.delete("1.0", tk.END)
        self._show_message("You", question)

        self.busy = True
        self.send_button.configure(state=tk.DISABLED)
        self._set_status("Thinking...")

        threading.Thread(
            target=self._ask_tutor,
            args=(question, self.learning_level),
            daemon=True,
        ).start()

        return "break"

    def _ask_tutor(self, question, learning_level):
        try:
            context = {}

            if self.context_provider is not None:
                context = self.context_provider() or {}

            camera_active = context.get("camera_active", False)

            answer = self.tutor.ask(
                question,
                current_mudra=(
                    context.get("mudra")
                    if camera_active else None
                ),
                confidence=(
                    context.get("confidence")
                    if camera_active else None
                ),
                learning_level=learning_level,
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
                    self._start_pending_practice_feedback()


                elif kind == "image_generated":

                    mudra_name, image_path = payload

                    self.image_generation_in_progress.discard(
                        mudra_name
                    )

                    # Save the dynamically generated image path.
                    self.generated_image_cache[mudra_name] = image_path

                    # Display only if this is still the selected image.
                    if self.image_panel.current_mudra == mudra_name:

                        self.image_panel.set_mudra(
                            mudra_name,
                            generated_image_path=image_path
                        )

                        self._set_status(
                            f"Image generated for {mudra_name}."
                        )


                elif kind == "image_generation_error":

                    mudra_name, error = payload

                    self.image_generation_in_progress.discard(
                        mudra_name
                    )

                    print(
                        f"Cloudflare image generation failed: {error}"
                    )

                    if self.image_panel.current_mudra == mudra_name:

                        error_message = str(error)

                        if "8007" in error_message:

                            status = (
                                "Cloudflare rejected the image prompt.\n\n"
                                "Please try again with a different "
                                "educational description."
                            )

                        else:

                            status = (
                                "Image generation failed.\n\n"
                                "Please check your Cloudflare API "
                                "credentials, account and quota."
                            )

                        self.image_panel.set_mudra(
                            mudra_name,
                            status_message=status
                        )

                        self._set_status(
                            "Image generation unavailable."
                        )

                elif kind == "error":
                    self._show_message(
                        "Tutor",
                        "Sorry, I couldn't complete that request. "
                        "Please try again.\n\nDetails: " + payload,
                    )
                    self.busy = False
                    self.send_button.configure(state=tk.NORMAL)
                    self._set_status("Request failed")
                    self._start_pending_practice_feedback()

                elif kind == "practice_feedback":

                    self._show_message(
                        "Practice Tutor",
                        payload
                    )

                    self.auto_feedback_busy = False

                    self._start_pending_practice_feedback()


                elif kind == "practice_feedback_error":

                    self.auto_feedback_busy = False

                    self._set_status(
                        "Automatic practice feedback failed."
                    )

                    print("Practice feedback error:", payload)

                    self._start_pending_practice_feedback()

        

        except queue.Empty:
            pass

        self.root.after(100, self._process_messages)

    def _clear_conversation(self):
        if self.busy or self.auto_feedback_busy:
            self._set_status(
                "Wait for the current response before starting a new conversation."
            )
            return

        if self.tutor is not None:
            self.tutor.reset_conversation()

        self.chat_area.configure(state=tk.NORMAL)
        self.chat_area.delete("1.0", tk.END)
        self.chat_area.configure(state=tk.DISABLED)
        # Clear teaching and practice contexts.
        self.current_teaching_mudra = None
        self.practice_target_mudra = None

        # Clear image display selection.
        self.image_display_context = None

        self.detected_mudra = None
        self.camera_active = False

        self.image_panel.clear()
        self.image_panel.pack_forget()

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

    def _start_camera(self):

        if self.camera_active:
            return

        if self.on_camera_start:

            # Use the currently taught mudra as the
            # default practice target.
            self.practice_target_mudra = (
                self.current_teaching_mudra
            )

            self.detected_mudra = None

            self.camera_active = True

            self.image_display_context = "practice"

# Initially display the intended practice target.
            if self.practice_target_mudra:
                self._request_mudra_image(
                    self.practice_target_mudra
                )

            self.on_camera_start()

            self.camera_start_button.configure(
                state=tk.DISABLED
            )

            self.camera_stop_button.configure(
                state=tk.NORMAL
            )

            if self.practice_target_mudra:
                self._set_status(
                    f"Practise your {self.practice_target_mudra} mudra."
                )
            else:
                self._set_status(
                    "Camera practice started. Select a mudra to practise."
                )

    def _stop_camera(self):

        if self.on_camera_stop:
            self.on_camera_stop()

            self.camera_start_button.configure(
                state=tk.NORMAL
            )

            self.camera_stop_button.configure(
                state=tk.DISABLED
            )

        # Phase 6: Reset prediction stability
        self.candidate_mudra = None
        self.candidate_count = 0
        self.stable_mudra = None


        # Stop camera state.
        self.camera_active = False

        # Reset practice context.
        self.practice_target_mudra = None
        self.detected_mudra = None

        # Reset displayed context.
        self.image_display_context = None

        # Clear pending feedback.
        self.pending_practice_mudra = None

        # Clear pending automatic feedback.
        self.pending_practice_mudra = None

        # Restore the teaching image if a lesson is active.
        if self.current_teaching_mudra:

            self.show_mudra_images(
                self.current_teaching_mudra
            )

        else:
            self.image_panel.clear()
            self.image_panel.pack_forget()

        self._set_status("Camera practice stopped.")



    def _refresh_recognition_status(self):

        if self.closed:
            return

        if self.context_provider is not None:
            context = self.context_provider() or {}
            self._handle_practice_prediction(context)

            if not context.get("camera_active", False):
                text = "Camera: Off"

            elif not context.get("mudra"):
                text = "Camera: On | No hand detected"

            else:
                mudra = context["mudra"]
                confidence = context.get("confidence")

                if confidence is not None:
                    text = (
                        f"Detected: {mudra} "
                        f"({float(confidence) * 100:.1f}%)"
                    )
                else:
                    text = f"Detected: {mudra}"

            self.recognition_label.configure(text=text)

        self.root.after(300, self._refresh_recognition_status)

    def _handle_practice_prediction(self, context):

        if not context.get("camera_active"):
            self.candidate_mudra = None
            self.candidate_count = 0
            return

        mudra = context.get("mudra")
        confidence = context.get("confidence")

        if not mudra or confidence is None:
            self.candidate_mudra = None
            self.candidate_count = 0
            return

        if confidence < self.confidence_threshold:
            self.candidate_mudra = None
            self.candidate_count = 0
            return

        if mudra == self.candidate_mudra:
            self.candidate_count += 1
        else:
            self.candidate_mudra = mudra
            self.candidate_count = 1

        if self.candidate_count < self.required_stable_samples:
            return

        # Ignore repeated stable predictions.
        if mudra == self.stable_mudra:
            return

        self.stable_mudra = mudra

        # New stable mudra detected.
        self._on_stable_mudra_detected(
            mudra,
            confidence
        )


    def _on_stable_mudra_detected(self, mudra, confidence):
        """
        Handle a newly recognised stable practice mudra.
        """

        if not self.camera_active:
            return

        # Update actual camera detection.
        self.detected_mudra = mudra

        # Display the detected mudra's generated image.
        self.show_practice_mudra_images(mudra)

        print("Teaching Mudra:", self.current_teaching_mudra)
        print("Practice Target:", self.practice_target_mudra)
        print("Detected Mudra:", self.detected_mudra)
        print("Displayed Context:", self.image_display_context)

        if self.practice_target_mudra:

            if mudra == self.practice_target_mudra:
                self._set_status(
                    f"Correct mudra detected: {mudra}"
                )

            else:
                self._set_status(
                    f"Target: {self.practice_target_mudra} | "
                    f"Detected: {mudra}"
                )

        else:
            self._set_status(
                f"Detected mudra: {mudra}"
            )

        self.pending_practice_mudra = (mudra, confidence)

        self._start_pending_practice_feedback()
      
    def _start_pending_practice_feedback(self):

        if self.closed:
            return

        if self.tutor is None:
            return

        if self.busy or self.auto_feedback_busy:
            self._set_status(
                "Please wait for the current tutor response."
            )
            return "break"

        if self.pending_practice_mudra is None:
            return

        mudra, confidence = self.pending_practice_mudra

        self.pending_practice_mudra = None
        self.auto_feedback_busy = True

        threading.Thread(
            target=self._generate_practice_feedback,
            args=(mudra, confidence),
            daemon=True
        ).start()


    def _generate_practice_feedback(self, mudra, confidence):

        try:

            question = (
                f"The learner is practising Bharatanatyam. "
                f"The SVM has consistently predicted {mudra} "
                f"with {confidence * 100:.1f}% confidence. "
                f"Provide brief, relevant practice guidance "
                f"for this mudra. Explain its traditional "
                f"formation and one or two common mistakes. "
                f"Remember that the SVM cannot verify exact "
                f"finger positioning. Avoid repeating "
                f"previous feedback unnecessarily."
            )

            answer = self.tutor.ask(
                question,
                current_mudra=mudra,
                confidence=confidence,
                learning_level=self.learning_level
            )

            self.messages.put(
                ("practice_feedback", answer)
            )

        except Exception as exc:

            self.messages.put(
                ("practice_feedback_error", str(exc))
            )


def main():
    root = tk.Tk()
    MudraTutorChat(root)
    root.mainloop()


if __name__ == "__main__":
    main()
