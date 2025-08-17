import tkinter as tk
from tkinter import messagebox


class SafetyAlertGUI:
    def __init__(self, on_timeout_or_no_understanding, message_text, required_phrase):
        self.alert_active = False
        self.on_timeout_or_no_understanding = on_timeout_or_no_understanding
        self.message_text = message_text
        self.required_phrase = required_phrase
        self.root = None
        self.countdown_label = None
        self.input_entry = None

    def show_alert(self):
        if self.alert_active:
            return
        self.alert_active = True
        self.create_alert_window()

    def create_alert_window(self):
        self.root = tk.Tk()
        self.root.title("Alerta de Seguridad")
        self.root.geometry("600x400")
        self.root.configure(bg="#e6f0fa")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        self.root.attributes("-topmost", True)
        self.root.lift()
        self.root.focus_force()

        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.root.winfo_screenheight() // 2) - (400 // 2)
        self.root.geometry(f"600x400+{x}+{y}")

        main_frame = tk.Frame(self.root, bg="#e6f0fa", padx=30, pady=30)
        main_frame.pack(fill="both", expand=True)

        tk.Label(
            main_frame,
            text="⚠️ Alerta de Seguridad ⚠️",
            font=("Arial", 20, "bold"),
            fg="#2c3e50",
            bg="#e6f0fa",
        ).pack(pady=(20, 30))

        tk.Label(
            main_frame,
            text=self.message_text.strip(),
            font=("Arial", 14),
            fg="#34495e",
            bg="#e6f0fa",
            justify="left",
        ).pack(pady=(0, 20))

        tk.Label(
            main_frame,
            text="Para continuar, escribe exactamente la siguiente frase:",
            font=("Arial", 14),
            fg="#34495e",
            bg="#e6f0fa",
        ).pack(pady=(0, 10))

        tk.Label(
            main_frame,
            text=f"'{self.required_phrase}'",
            font=("Arial", 14, "italic"),
            fg="#34495e",
            bg="#e6f0fa",
        ).pack(pady=(0, 20))

        self.input_entry = tk.Entry(
            main_frame,
            width=35,
            font=("Arial", 14),
            justify="center",
            bg="#ffffff",
            fg="#2c3e50",
            bd=2,
            relief="flat",
        )
        self.input_entry.pack(pady=(0, 20))
        self.input_entry.bind("<Return>", lambda event: self.handle_response())
        self.input_entry.focus_set()

        tk.Button(
            main_frame,
            text="Confirmar y Continuar",
            font=("Arial", 14, "bold"),
            bg="#3498db",
            fg="white",
            padx=30,
            pady=15,
            command=self.handle_response,
            relief="flat",
            activebackground="#2980b9",
        ).pack(pady=20)

        self.countdown_label = tk.Label(
            main_frame,
            text="Tiempo restante: 10 segundos",
            font=("Arial", 12, "bold"),
            fg="#f1c40f",
            bg="#e6f0fa",
        )
        self.countdown_label.pack()

        self.start_countdown(remaining=10)
        self.root.grab_set()
        self.root.mainloop()

    def start_countdown(self, remaining=10):
        if remaining > 0 and self.alert_active:
            self.countdown_label.config(text=f"Tiempo restante: {remaining} segundos")
            self.root.after(1000, lambda: self.start_countdown(remaining - 1))
        else:
            if self.alert_active:
                self.countdown_label.config(text="¡Tiempo agotado!")
                self.alert_active = False
                self.on_timeout_or_no_understanding()
                self.root.destroy()

    def handle_response(self):
        user_input = self.input_entry.get().strip()
        if user_input == self.required_phrase:
            self.alert_active = False
            print("Usuario confirmó correctamente.")
            messagebox.showinfo(
                "¡Éxito!", "Has confirmado las reglas de seguridad. Puedes continuar."
            )
            self.root.destroy()
        else:
            self.alert_active = False
            print("Frase incorrecta - cerrando el juego por seguridad.")
            messagebox.showwarning(
                "¡Frase Incorrecta!",
                "La frase que escribiste no es correcta. El juego se cerrará por tu seguridad.",
            )
            self.on_timeout_or_no_understanding()
            self.root.destroy()
