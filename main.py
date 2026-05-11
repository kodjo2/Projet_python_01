# prototype d'affichage de mindmap en radial et forum
# avec possibilité d'éditer les nodes (si auteur) ou d'en ajouter en dessous    
# JCY pour SI-CA1 (projet Python) - 2025-2026 -v0.1
# 13 avril 2026
# main.py : affichage de la fenêtre principale, gestion de la connexion et des différentes vues (tables + mindmap)

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, simpledialog
from login import show_login, show_register
from tree_display import display_array
from model import (
    get_maps,
    get_nodes_for_map,
    get_users,
    get_nodes,
    insert_map,
    update_map_title,
    delete_map,
    update_node_text,
    delete_node,
    insert_node,
)
from utils.session import Session
import math

# Variable globale pour le mode DB
db_mode = None
current_map_id = None

# Vérification de connexion
def check_auth():
    return Session.is_authenticated()

# affichage des maps 
def display_users():
    result = get_users(db_mode)
    frm_result.tree = display_array(frm_result, result)
    # pas de double-clic ici (évite d'ouvrir une map avec un mauvais id)
       
def display_maps():
    result = get_maps(db_mode)
    frm_result.tree = display_array(frm_result, result)
    frm_result.tree.bind("<Double-1>", on_map_double_click) # double clic pour afficher le mindmap dans right_frame selon le mode sélectionné (tree, radial ou forum)
    frm_result.tree.bind("<Button-3>", on_map_right_click)
       
def display_nodes():
    result = get_nodes(db_mode)
    frm_result.tree = display_array(frm_result, result)
    # pas de double-clic ici (évite d'ouvrir une map avec un mauvais id)
       
# traitement de l'affichage d'un mindmap selon le mode sélectionné (tree, radial ou forum)
def on_map_double_click(event):
    selected = frm_result.tree.selection()
    if selected:
        item = frm_result.tree.item(selected[0])
        values = item['values']
        map_id = values[0]  # Supposons que id est la première colonne
        display_mindmap(map_id)


def on_map_right_click(event):
    """Menu contextuel sur la liste des maps (CRUD maps)."""
    tree = frm_result.tree
    row_id = tree.identify_row(event.y)
    if not row_id:
        # clic dans le vide -> proposer seulement "Nouveau map" si connecté
        show_map_context_menu(event, map_row=None)
        return

    tree.selection_set(row_id)
    item = tree.item(row_id)
    values = item.get("values") or []
    if not values:
        show_map_context_menu(event, map_row=None)
        return

    # get_maps renvoie: id, title, author_id (dans cet ordre)
    map_row = {"id": values[0], "title": values[1] if len(values) > 1 else "", "author_id": values[2] if len(values) > 2 else None}
    show_map_context_menu(event, map_row=map_row)


def show_map_context_menu(event, map_row=None):
    menu = tk.Menu(root, tearoff=0)

    # Nouveau map: nécessite d'être connecté
    menu.add_command(label="Insérer un nouveau map", command=insert_new_map)

    if map_row is not None:
        menu.add_command(label="Éditer le titre", command=lambda r=map_row: edit_map_title(r))
        menu.add_command(label="Supprimer", command=lambda r=map_row: delete_map_action(r))

    # griser si pas connecté
    if not Session.is_authenticated():
        menu.entryconfig("Insérer un nouveau map", state="disabled")
        if map_row is not None:
            menu.entryconfig("Éditer le titre", state="disabled")
            menu.entryconfig("Supprimer", state="disabled")

    menu.post(event.x_root, event.y_root)


def insert_new_map():
    if not Session.is_authenticated():
        messagebox.showerror("Erreur", "Tu dois être connecté")
        return

    title = simpledialog.askstring("Nouveau map", "Titre du mindmap:")
    if title is None:
        return
    title = title.strip()
    if not title:
        messagebox.showerror("Erreur", "Titre vide")
        return

    insert_map(title, Session.id, db_mode=db_mode)
    display_maps()


def edit_map_title(map_row):
    if not Session.is_authenticated():
        messagebox.showerror("Erreur", "Tu dois être connecté")
        return
    # Option: n'autoriser que l'auteur
    if Session.id != map_row.get("author_id"):
        messagebox.showerror("Erreur", "Tu ne peux modifier que tes propres maps")
        return

    new_title = simpledialog.askstring("Éditer", "Nouveau titre:", initialvalue=map_row.get("title", ""))
    if new_title is None:
        return
    new_title = new_title.strip()
    if not new_title:
        messagebox.showerror("Erreur", "Titre vide")
        return

    update_map_title(map_row.get("id"), new_title, db_mode=db_mode)
    display_maps()


def delete_map_action(map_row):
    if not Session.is_authenticated():
        messagebox.showerror("Erreur", "Tu dois être connecté")
        return
    if Session.id != map_row.get("author_id"):
        messagebox.showerror("Erreur", "Tu ne peux supprimer que tes propres maps")
        return

    if not messagebox.askyesno("Supprimer", "Supprimer ce mindmap ?"):
        return

    try:
        delete_map(map_row.get("id"), db_mode=db_mode)
    except Exception as e:
        messagebox.showerror("Erreur", f"Suppression impossible: {e}")
        return

    # nettoyer la vue droite si la map supprimée était affichée
    global current_map_id
    if current_map_id == map_row.get("id"):
        current_map_id = None
        for widget in right_frame.winfo_children():
            widget.destroy()
        tk.Label(right_frame, text="Zone Mindmap", font=("Arial", 16)).pack(expand=True)

    display_maps()

# affichage du mindmap selon le mode sélectionné
def display_mindmap(map_id):
    global current_map_id
    current_map_id = map_id
    nodes = get_nodes_for_map(map_id,db_mode)
    # Nettoyer right_frame
    for widget in right_frame.winfo_children():
        widget.destroy()
    # Afficher les nodes selon le mode
    if nodes:
        mode = display_mode.get()
        if mode == 'tree':
            display_mindmap_tree(right_frame, nodes)
        elif mode == 'forum':
            display_mindmap_forum(right_frame, nodes)
        elif mode == 'radial':
                    display_mindmap_radial(right_frame, nodes)

    else:
        tk.Label(right_frame, text="Aucun node pour ce mindmap").pack()

def refresh_mindmap():
    if current_map_id is not None:
        display_mindmap(current_map_id)

# Affichage du mindmap en TreeView (version simple)
def display_mindmap_tree(frame, nodes):

    # Créer le Treeview
    tree = ttk.Treeview(frame, columns=(), show='tree')  # Pas de colonnes supplémentaires
    tree.heading('#0', text='Text')

    # Police plus petite et interligne ajusté pour beaucoup d'enregistrements
    style = ttk.Style()
    style.configure("Right.Treeview", font=("TkDefaultFont", 20), rowheight=35)
    tree.configure(style="Right.Treeview")

    # Fonction récursive pour insérer les nodes
    def insert_nodes(parent, parent_id=None):
        for node in nodes:
            if node['parent_id'] == parent_id:
                item = tree.insert(parent, 'end', text=node['text'])  # Seulement le text
                insert_nodes(item, node['id'])

    insert_nodes('')

    # Scrollbars
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.pack(side='left', fill='both', expand=True)
    vsb.pack(side='right', fill='y')
    hsb.pack(side='bottom', fill='x')

# Affichage du mindmap en forum (version plus compacte et adaptée à l'affichage de nombreux nodes, avec possibilité d'éditer les nodes ou d'en ajouter en dessous)
def display_mindmap_forum(frame, nodes):
    container = tk.Frame(frame)
    container.pack(fill='both', expand=True)

    canvas = tk.Canvas(container, bg='white')
    vsb = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    hsb = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)

    canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")
    canvas.pack(side="left", fill="both", expand=True)

    # Mise à jour de la zone scrollable
    def update_scroll_region(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    canvas.bind("<Configure>", update_scroll_region)

    # Trouver le root
    root_node = next((n for n in nodes if n['parent_id'] is None or n['parent_id'] == 0), None)
    if not root_node:
        return

    canvas_width = 800
    canvas_height = 600
    node_height = 25  # Réduit à 30 pour moins de place verticale

    # Crée un rectangle arrondi (pour les nodes du forum)
    def create_rounded_rectangle(canvas, x1, y1, x2, y2, radius=10, **kwargs):

        # sécurité : éviter un rayon trop grand
        radius = min(radius, abs(x2 - x1)//2, abs(y2 - y1)//2)

        points = [ x1 + radius, y1, x2 - radius, y1,
            x2, y1, x2, y1 + radius,
            x2, y2 - radius, x2, y2,
            x2 - radius, y2, x1 + radius, y2,
            x1, y2, x1, y2 - radius,
            x1, y1 + radius, x1, y1,
            x1 + radius, y1 ]

        return canvas.create_polygon(points, smooth=True, **kwargs)
    # Place les nodes en mode forum de manière récursive
    def place_forum(node, x, y, width_percent, level=0):
        width = int(canvas_width * width_percent / 100)
        item = create_rounded_rectangle(canvas, x, y, x + width, y + node_height, radius=8, fill='lightblue' if level == 0 else node["color"], outline='black')
        canvas.create_text(x + width/2, y + node_height/2, text=node['text'][:40], anchor='center', font=("Arial", 12))  # Police augmentée
        # Binder le clic droit sur le node pour éditer
        canvas.tag_bind(item, "<Button-3>", lambda e, n=node: edit_node(e, n)) # n contient les infos du node pour l'édition    
        children = [n for n in nodes if n['parent_id'] == node['id']]
        total_height = node_height + 10  # hauteur du node + marge
        if children:
            child_x = x + int(canvas_width * 20 / 100)  # décalage de 20%
            child_width_percent = max(width_percent - 5, 10)  # diminuer de 5% par niveau, min 10%
            current_y = y + node_height + 10
            for child in children:
                child_height = place_forum(child, child_x, current_y, child_width_percent, level+1)
                current_y += child_height
                total_height += child_height
        return total_height

    place_forum(root_node, 20, 20, 50) # le root prend 50% de la largeur, les enfants 45%, etc. 
    update_scroll_region()


def display_mindmap_radial(frame, nodes):
    # Canvas plein écran dans la zone de droite
    canvas = tk.Canvas(frame, bg="white")
    canvas.pack(fill="both", expand=True)

    # déterminer la racine (parent_id None ou 0)
    root_node = next((n for n in nodes if n.get('parent_id') is None or n.get('parent_id') == 0), None)
    if not root_node:
        canvas.create_text(20, 20, text="Pas de racine détectée", anchor="nw")
        return

    # indexer enfants par parent_id
    children_by_parent = {}
    by_id = {}
    for n in nodes:
        by_id[n.get("id")] = n
        children_by_parent.setdefault(n.get("parent_id"), []).append(n)

    # BFS profondeur
    depth = {root_node["id"]: 0}
    queue = [root_node["id"]]
    while queue:
        nid = queue.pop(0)
        for child in children_by_parent.get(nid, []):
            cid = child.get("id")
            if cid is None:
                continue
            if cid not in depth:
                depth[cid] = depth[nid] + 1
                queue.append(cid)

    max_depth = max(depth.values()) if depth else 0

    # regrouper ids par profondeur
    level_nodes = {}
    for nid, d in depth.items():
        level_nodes.setdefault(d, []).append(nid)

    def draw():
        canvas.delete("all")
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        cx, cy = w // 2, h // 2

        radius_step = 90
        node_r = 22

        positions = {}

        for d in range(0, max_depth + 1):
            ids = level_nodes.get(d, [])
            if not ids:
                continue

            if d == 0:
                positions[ids[0]] = (cx, cy)
                continue

            ring_r = d * radius_step
            count = len(ids)
            for i, nid in enumerate(ids):
                angle = (2 * math.pi * i) / max(count, 1)
                x = cx + int(ring_r * math.cos(angle))
                y = cy + int(ring_r * math.sin(angle))
                positions[nid] = (x, y)

        # traits
        for child in nodes:
            cid = child.get("id")
            pid = child.get("parent_id")
            if pid in positions and cid in positions:
                x1, y1 = positions[pid]
                x2, y2 = positions[cid]
                canvas.create_line(x1, y1, x2, y2, fill="#555", width=2)

        # cercles + texte
        for nid, (x, y) in positions.items():
            n = by_id.get(nid, {})
            fill = n.get("color") or "lightblue"
            canvas.create_oval(x - node_r, y - node_r, x + node_r, y + node_r, fill=fill, outline="black")
            canvas.create_text(x, y, text=str(n.get("text", ""))[:12], font=("Arial", 10), width=90)

    canvas.bind("<Configure>", lambda e: draw())
    draw()


# Cette fonction propose 3 actions sur un node : éditer le texte, supprimer le node ou insérer un nouveau node en dessous
def edit_node(event, node):
    #if not check_auth():
    #    return
    menu = tk.Menu(root, tearoff=0)
    menu.add_command(label="Éditer", command=lambda: edit_text(node))
    menu.add_command(label="Supprimer", command=lambda: delete_node_action(node))
    menu.add_command(label="Insérer en dessous", command=lambda: insert_below(node))
    menu.post(event.x_root, event.y_root)

# propose d'éditer le texte d'un node (seulement si l'utilisateur est l'auteur du node)
def edit_text(node):
    if not Session.is_authenticated():
        messagebox.showerror("Erreur", "Tu dois être connecté")
        return
    if Session.id != node.get("author_id"):
        messagebox.showerror("Erreur", "Tu ne peux modifier que tes propres nodes")
        return

    new_text = simpledialog.askstring("Éditer", "Nouveau texte:", initialvalue=node.get("text", ""))
    if new_text is None:
        return
    new_text = new_text.strip()
    if not new_text:
        messagebox.showerror("Erreur", "Texte vide")
        return

    update_node_text(node.get("id"), new_text, db_mode=db_mode)
    refresh_mindmap()

# propose de supprimer un node (seulement si l'utilisateur est l'auteur du node)
def delete_node_action(node):
    if not Session.is_authenticated():
        messagebox.showerror("Erreur", "Tu dois être connecté")
        return
    if Session.id != node.get("author_id"):
        messagebox.showerror("Erreur", "Tu ne peux supprimer que tes propres nodes")
        return

    if not messagebox.askyesno("Supprimer", "Supprimer ce node ?"):
        return

    try:
        delete_node(node.get("id"), db_mode=db_mode)
    except Exception as e:
        messagebox.showerror("Erreur", f"Suppression impossible: {e}")
        return

    refresh_mindmap()

# propose d'insérer un nouveau node en dessous du node sélectionné (le nouveau node aura comme parent le node sélectionné)
def insert_below(node):
    if not Session.is_authenticated():
        messagebox.showerror("Erreur", "Tu dois être connecté")
        return
    if current_map_id is None:
        messagebox.showerror("Erreur", "Aucune map sélectionnée")
        return

    text = simpledialog.askstring("Insérer", "Texte du nouveau node:")
    if text is None:
        return
    text = text.strip()
    if not text:
        messagebox.showerror("Erreur", "Texte vide")
        return

    parent_id = node.get("id")
    # level: on fait simple (même level+1 si présent)
    level = (node.get("level") or 0) + 1
    insert_node(current_map_id, parent_id, Session.id, text, level=level, db_mode=db_mode)
    refresh_mindmap()


# Permet de changer le mode de la base de données (local ou remote) et met à jour la variable globale db_mode
def set_db_mode(mode):
    global db_mode
    if (mode != db_mode): # éviter de faire un logout inutile qui ferait perdre la connexion à l'utilisateur
        db_mode = mode
        #Session.logout()  # forcer le logout pour éviter les incohérences
        lbl_user.config(text="Non connecté")
        lbl_db_mode.config(text=f"Mode DB: {db_mode}", bg="red" if db_mode == "remote" else "green", fg="white")
        display_maps()  # rafraîchir l'affichage des maps pour éviter les incohérences

# connexion (appelle une fenêtre de login)
def login():
    show_login(root, db_mode=db_mode)
    if Session.is_authenticated():
        lbl_user.config(text=f"Connecté en tant que {Session.pseudo}") 


def register():
    show_register(root, db_mode=db_mode)
    if Session.is_authenticated():
        lbl_user.config(text=f"Connecté en tant que {Session.pseudo}")


def logout():
    Session.logout()
    lbl_user.config(text="Non connecté")


# fenêtre principale
root = tk.Tk()

root.minsize(1200, 800)  # Ajusté pour accommoder les deux frames
root.title("Mindmaps - Version de base v0.1")

# Création du menu
menubar = tk.Menu(root)

# Menu Afficher
display_menu = tk.Menu(menubar, tearoff=0)
display_menu.add_command(label="Users", command=display_users)
display_menu.add_command(label="Maps", command=display_maps)
display_menu.add_command(label="Nodes", command=display_nodes)
menubar.add_cascade(label="Afficher", menu=display_menu)

# Menu Login/Register
login_menu = tk.Menu(menubar, tearoff=0)
login_menu.add_command(label="Login", command=login)
login_menu.add_command(label="Register", command=register)
login_menu.add_separator()
login_menu.add_command(label="Logout", command=logout)
menubar.add_cascade(label="Login/Register", menu=login_menu)

# Menu local/remote
db_menu = tk.Menu(menubar, tearoff=0)
db_menu.add_command(label="Local", command=lambda: set_db_mode('local'))
db_menu.add_command(label="Remote", command=lambda: set_db_mode('remote'))
menubar.add_cascade(label="Mode DB", menu=db_menu)

root.config(menu=menubar)

# Configuration du grid pour root
root.columnconfigure(0, minsize=500)  # Frame gauche de largeur fixe 500
root.columnconfigure(1, weight=1)     # Frame droite prend le reste
root.rowconfigure(0, weight=1)

# Frame gauche pour contrôles et affichage des tables
left_frame = tk.Frame(root, bg="lightgray", width=500)
left_frame.grid(column=0, row=0, sticky="ns")  # "ns" pour étirement vertical seulement

# Frame droite pour l'affichage du mindmap
right_frame = tk.Frame(root, bg="white")
right_frame.grid(column=1, row=0, sticky="nsew")

# Variable pour le mode d'affichage
display_mode = tk.StringVar(value='tree')

# Configuration du grid pour left_frame
left_frame.rowconfigure(3, weight=1)  # frm_result prend l'espace restant
left_frame.columnconfigure(0, weight=1)
left_frame.columnconfigure(1, weight=1)

# Information sur la connexion dans left_frame
lbl_user = tk.Label(left_frame, text="Non connecté")
lbl_user.grid(column=0, row=0, padx=10, pady=10)
# Information sur la base de données utilisée 
lbl_db_mode = tk.Label(left_frame, text="db_mode: local")
lbl_db_mode.grid(column=1, row=0, padx=10, pady=10)

# frame pour les boutons dans left_frame
frm_buttons = tk.Frame(left_frame, bg="lightblue")
frm_buttons.grid(column=0, row=1, pady=10)

# frame pour les options d'affichage
frm_options = tk.Frame(left_frame, bg="lightyellow")
frm_options.grid(column=0, row=2, pady=10)

tk.Label(frm_options, text="Mode d'affichage Mindmap:").pack(anchor='w')
tk.Radiobutton(frm_options, text="Treeview", variable=display_mode, value='tree', command=refresh_mindmap).pack(anchor='w')
tk.Radiobutton(frm_options, text="Forum", variable=display_mode, value='forum', command=refresh_mindmap).pack(anchor='w')
tk.Radiobutton(frm_options, text="Radial", variable=display_mode, value='radial', command=refresh_mindmap).pack(anchor='w')



# frame pour l'affichage des résultats dans left_frame
frm_result = tk.Frame(left_frame, bg="lightgreen")
frm_result.grid(column=0, row=3, columnspan=2, sticky="nsew", padx=10, pady=10)

# Placeholder pour le mindmap dans right_frame
tk.Label(right_frame, text="Zone Mindmap", font=("Arial", 16)).pack(expand=True)

# remplissage de frm_result
tk.Label(frm_result,text="RESULTS").pack()

# Affiche les maps au démarrage
set_db_mode("local")
display_maps()
root.mainloop()


