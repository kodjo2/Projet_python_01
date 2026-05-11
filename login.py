# Projet mindmaps : prototype d'affichage de mindmap en radial et forum 
# Attivon Kodjo pour SI-CA1 (projet Python) - 2025-2026
# 13 avril 2026
# login.py : affichage de la fenêtre de connexion

import tkinter as tk
from tkinter import messagebox
from model import check_login, create_user
from utils.session import Session

def show_login(parent, db_mode="local" ):
    if Session.is_authenticated():
        messagebox.showinfo("Info", f"Déjà connecté en tant que {Session.pseudo}")
        return
    win = tk.Toplevel(parent)
    win.title("Login")

    # Empêcher d'interagir avec parent
    win.transient(parent)   # attache au parent
    win.grab_set()          # rend la fenêtre modale


    tk.Label(win, text="Pseudo").grid(row=0, column=0)
    tk.Label(win, text="Mot de passe").grid(row=1, column=0, padx=20, pady=20)

    entry_pseudo = tk.Entry(win)
    entry_pseudo.grid(row=0, column=1)

    entry_pass = tk.Entry(win, show="*")
    entry_pass.grid(row=1, column=1, padx=20, pady=20)

    def attempt_login(db_mode=db_mode):
        user = check_login(entry_pseudo.get(), entry_pass.get(), db_mode)

        if user:
            Session.login(user["pseudo"], user["level"], user["id"])
            # messagebox.showinfo("OK", f"Bienvenue {user['pseudo']} !")
            win.destroy()
        else:
            messagebox.showerror("Erreur", "Login incorrect")

          

    def open_register():
        win.destroy()
        show_register(parent, db_mode)

    tk.Button(win, text="Se connecter", command=attempt_login).grid(row=2, column=0, columnspan=2)
    tk.Button(win, text="Register", command=open_register).grid(row=3, column=0, columnspan=2)
    
    
    # Empêche d'accéder à la fenêtre principale tant que login est ouvert
    parent.wait_window(win)

def show_register(parent, db_mode="local"):
    if Session.is_authenticated():
        messagebox.showinfo("Info", f"Déjà connecté en tant que {Session.pseudo}")
        return

    win = tk.Toplevel(parent)
    win.title("Register")

    # Empêcher d'interagir avec parent
    win.transient(parent)
    win.grab_set()

    tk.Label(win, text="Pseudo").grid(row=0, column=0)
    tk.Label(win, text="Mot de passe").grid(row=1, column=0, padx=20, pady=20)
    tk.Label(win, text="Confirmer").grid(row=2, column=0, padx=20, pady=20)
    tk.Label(win, text="Couleur (#RRGGBB)").grid(row=3, column=0)

    entry_pseudo = tk.Entry(win)
    entry_pseudo.grid(row=0, column=1)

    entry_pass1 = tk.Entry(win, show="*")
    entry_pass1.grid(row=1, column=1, padx=20, pady=20)

    entry_pass2 = tk.Entry(win, show="*")
    entry_pass2.grid(row=2, column=1, padx=20, pady=20)

    entry_color = tk.Entry(win)
    entry_color.insert(0, "#AADDFF")
    entry_color.grid(row=3, column=1)

    def attempt_register(db_mode=db_mode):
        pseudo = entry_pseudo.get().strip()
        p1 = entry_pass1.get()
        p2 = entry_pass2.get()
        color = entry_color.get().strip()

        if not pseudo or not p1 or not p2 or not color:
            messagebox.showerror("Erreur", "Tous les champs sont obligatoires")
            return

        if p1 != p2:
            messagebox.showerror("Erreur", "Les mots de passe ne correspondent pas")
            return

        if not (color.startswith("#") and len(color) == 7):
            messagebox.showerror("Erreur", "Couleur invalide. Exemple: #AABBCC")
            return

        try:
            user_id = create_user(pseudo, p1, color, level=1, db_mode=db_mode)
        except ValueError as e:
            messagebox.showerror("Erreur", str(e))
            return
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur DB: {e}")
            return

        Session.login(pseudo, 1, user_id)
        win.destroy()

    def back_to_login():
        win.destroy()
        show_login(parent, db_mode)

    tk.Button(win, text="Créer le compte", command=attempt_register).grid(row=4, column=0, columnspan=2, pady=(0, 8))
    tk.Button(win, text="Retour login", command=back_to_login).grid(row=5, column=0, columnspan=2)

    parent.wait_window(win)
