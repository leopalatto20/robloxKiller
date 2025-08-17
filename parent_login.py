import tkinter as tk
from tkinter import messagebox
import requests


class ParentLogin:
    def __init__(self):
        self.valid_id = None
        self.root = tk.Tk()
        self.root.title("Inicio de Sesión para Padres")
        self.root.geometry("600x400")
        self.root.configure(bg="#e6f0fa")
        self.root.resizable(False, False)
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.root.winfo_screenheight() // 2) - (400 // 2)
        self.root.geometry(f"600x400+{x}+{y}")

        main_frame = tk.Frame(self.root, bg="#e6f0fa", padx=30, pady=30)
        main_frame.pack(fill="both", expand=True)

        tk.Label(
            main_frame,
            text="¡Bienvenido, Papá! 👨‍👦",
            font=("Arial", 20, "bold"),
            fg="#2c3e50",
            bg="#e6f0fa",
        ).pack(pady=(20, 30))
        tk.Label(
            main_frame,
            text="Ingresa tu ID para continuar:",
            font=("Arial", 14),
            fg="#34495e",
            bg="#e6f0fa",
        ).pack(pady=(0, 10))

        self.entry = tk.Entry(
            main_frame,
            width=35,
            font=("Arial", 14),
            bd=2,
            relief="flat",
            bg="#ffffff",
            fg="#2c3e50",
        )
        self.entry.pack(pady=(0, 20))
        self.entry.focus_set()

        tk.Button(
            main_frame,
            text="Iniciar Sesión",
            font=("Arial", 14, "bold"),
            bg="#3498db",
            fg="white",
            padx=30,
            pady=15,
            relief="flat",
            activebackground="#2980b9",
            command=self.check_id,
        ).pack(pady=20)

    def check_id(self):
        parent_id = self.entry.get().strip()
        if not parent_id:
            messagebox.showerror("Error", "El ID no puede estar vacío.")
            return

        try:
            url = f"http://127.0.0.1:8000/api/check_parent/{parent_id}"
            response = requests.get(url)
            if response.status_code == 200 and response.json().get("valid"):
                messagebox.showinfo("Acceso concedido", "¡Bienvenido, papá! 👨‍👦")
                self.valid_id = parent_id
                self.root.quit()  # Termina mainloop
            else:
                messagebox.showerror("Acceso denegado", "ID inválido.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar al servidor:\n{e}")

    def run(self):
        self.root.mainloop()
        return self.valid_id
