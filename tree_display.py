# Projet mindmaps : prototype d'affichage de mindmap en radial et forum 
# Attivon Kodjo pour SI-CA1 (projet Python) - 2025-2026
# 13 avril 2026
# tree_display.py : affichage d'un tableau de données dans un TreeView

import tkinter as tk
from tkinter import ttk
from tkinter import font

def enable_treeview_sorting(tree: ttk.Treeview):
    """
    Active le tri en cliquant sur l'en-tête d'une colonne.
    Clique successif sur la même colonne => inverse asc/desc.
    """
    state = {"col": None, "desc": False}

    def to_key(value):
        # Tri "intelligent": num si possible, sinon texte
        if value is None:
            return (1, "")
        s = str(value).strip()
        if s == "":
            return (1, "")
        try:
            return (0, float(s.replace(",", ".")))
        except ValueError:
            return (1, s.casefold())

    def sort_column(col: str):
        items = list(tree.get_children(""))
        data = [(to_key(tree.set(iid, col)), iid) for iid in items]

        if state["col"] == col:
            state["desc"] = not state["desc"]
        else:
            state["col"] = col
            state["desc"] = False

        data.sort(reverse=state["desc"])

        for idx, (_, iid) in enumerate(data):
            tree.move(iid, "", idx)

        # (optionnel) indicateur dans le header
        for c in tree["columns"]:
            tree.heading(c, text=c, command=lambda cc=c: sort_column(cc))
        arrow = " ↓" if state["desc"] else " ↑"
        tree.heading(col, text=f"{col}{arrow}", command=lambda cc=col: sort_column(cc))

    for col in tree["columns"]:
        tree.heading(col, command=lambda c=col: sort_column(c))

# C'est la fonction principale pour afficher un tableau de données dans un TreeView
# data doit être une liste de dictionnaires, où chaque dictionnaire représente une ligne et les clés    sont les noms des colonnes
# Exemple : data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
def display_array(frame, data):
    # nettoyer la frame
    for widget in frame.winfo_children():
        widget.destroy()

    # récupérer automatiquement les colonnes
    if not data or not isinstance(data, list) or not isinstance(data[0], dict):
        raise ValueError("data doit être une liste de dictionnaires non vide.")

    columns = list(data[0].keys())

    # --- FRAME POUR LE TREEVIEW + SCROLLBARS ---
    container = ttk.Frame(frame)
    container.pack(fill="both", expand=True)

    # Scrollbars
    vsb = ttk.Scrollbar(container, orient="vertical")
    hsb = ttk.Scrollbar(container, orient="horizontal")

    tree = ttk.Treeview(
        container,
        columns=columns,
        show="headings",
        yscrollcommand=vsb.set,
        xscrollcommand=hsb.set
    )

    # Configurer le style pour le TreeView de gauche (tables)
    style = ttk.Style()
    style.configure("Left.Treeview", font=("Arial", 10), rowheight=20)
    tree.configure(style="Left.Treeview")

    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)

    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")
    tree.pack(fill="both", expand=True)

    # colonnes + largeur automatique
    for col in columns:
        tree.heading(col, text=col)
        tree.heading(col, anchor="w") # alignement à gauche
        tree.column(col, width=tkFontMeasure(tree, col, data), stretch=True)

    # insérer données
    insert_rows(tree, data, columns)

    # activer le tri par clic sur les en-têtes
    enable_treeview_sorting(tree)
    return tree


def insert_rows(tree, data, columns):
    # effacer existant
    for row in tree.get_children():
        tree.delete(row)

    for row_dict in data:
        values = [row_dict[col] for col in columns]
        tree.insert("", tk.END, values=values)


def tkFontMeasure(tree, col, data):
    """ Calcule automatiquement la largeur idéale d’une colonne """
    f = font.nametofont("TkDefaultFont")

    # largeur selon l’en-tête
    width = f.measure(col)

    # largeur selon les données
    for row in data:
        cell_value = str(row[col])
    width = max(width, f.measure(cell_value))

    # un petit padding et limite à 200px
    return min(width + 20, 200)