# Projet mindmaps : prototype d'affichage de mindmap en radial et forum 
# JCY pour SI-CA1 (projet Python) - 2025-2026
# 13 avril 2026
# model.py : définition des fonctions pour interagir avec la base de données

import mysql.connector
import bcrypt
from utils.config import get_db_config

# Fonction pour obtenir une connexion à la base de données
def get_connection(db_mode="local"):
    cfg = get_db_config(db_mode)
    port = cfg.get("port")

    return mysql.connector.connect(
        host=cfg["host"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        port=int(port) if port else 3306
    )

# renvoie le résultat d'une requête SQL en mode dictionnaire
def fetch_all(sql_query, params=None, db_mode="local"):
    db = get_connection(db_mode)
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(sql_query, params or ())
        return cursor.fetchall()
    finally:
        cursor.close()
        db.close()


# renvoie la liste des maps (sans les nodes) pour l'affichage de la page d'accueil
def get_maps(db_mode):
    return fetch_all("select id, title, author_id from maps", None, db_mode)


def insert_map(title, author_id, db_mode="local"):
    """Insère une map et retourne son id."""
    db = get_connection(db_mode)
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO maps (title, author_id) VALUES (%s, %s)",
            (title, author_id),
        )
        db.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        db.close()


def update_map_title(map_id, new_title, db_mode="local"):
    """Met à jour le titre d'une map."""
    db = get_connection(db_mode)
    cursor = db.cursor()
    try:
        cursor.execute("UPDATE maps SET title=%s WHERE id=%s", (new_title, map_id))
        db.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        db.close()


def delete_map(map_id, db_mode="local"):
    """Supprime une map (attention: si nodes existent, la DB peut refuser)."""
    db = get_connection(db_mode)
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM maps WHERE id=%s", (map_id,))
        db.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        db.close()


# renvoie la liste de tous les nodes d'un map (avec le pseudo de l'auteur et sa couleur)
def get_nodes_for_map(map_id, db_mode):
    return fetch_all("select nodes.id, parent_id, author_id, text, nodes.level,users.color " \
    "from nodes inner join users on nodes.author_id = users.id " \
    "where map_id=%s", (map_id,), db_mode)

# fonctions pour insérer, mettre à jour et supprimer des maps et des nodes
def get_users(db_mode="local"):
    """Renvoie la table users (sans le hash) pour affichage en TreeView."""
    return fetch_all("SELECT id, pseudo, level FROM users", None, db_mode)

# fonction pour insérer un node (retourne l'id du node créé)
def get_nodes(db_mode="local"):
    """Renvoie une vue partielle de la table nodes pour affichage en TreeView."""
    return fetch_all(
        "SELECT map_id, parent_id, author_id, text, level FROM nodes",
        None,
        db_mode
    )


def update_node_text(node_id, new_text, db_mode="local"):
    """Met à jour le texte d'un node."""
    db = get_connection(db_mode)
    cursor = db.cursor()
    try:
        cursor.execute("UPDATE nodes SET text=%s WHERE id=%s", (new_text, node_id))
        db.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        db.close()


def delete_node(node_id, db_mode="local"):
    """Supprime un node (attention: si des enfants existent, la DB peut refuser)."""
    db = get_connection(db_mode)
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM nodes WHERE id=%s", (node_id,))
        db.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        db.close()


def insert_node(map_id, parent_id, author_id, text, level=0, db_mode="local"):
    """Insère un node et retourne son id."""
    db = get_connection(db_mode)
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO nodes (map_id, parent_id, author_id, text, level) VALUES (%s, %s, %s, %s, %s)",
            (map_id, parent_id, author_id, text, level),
        )
        db.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        db.close()

# fonction pour vérifier les identifiants de connexion d'un utilisateur (retourne les infos de l'utilisateur si ok, sinon None)
def check_login(pseudo, password, db_mode="local"):
    """Retourne {id, pseudo, level} si OK, sinon None. Ne retourne jamais le hash."""
    db = get_connection(db_mode)
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, pseudo, hash, level FROM users WHERE pseudo=%s", (pseudo,))
        row = cursor.fetchone()
        if not row:
            return None

        stored = row.get("hash")
        if stored is None:
            return None
        if isinstance(stored, str):
            stored = stored.encode("utf-8")

        # Vérifier le mot de passe avec bcrypt
        if bcrypt.checkpw(password.encode("utf-8"), stored):
            return {"id": row["id"], "pseudo": row["pseudo"], "level": row["level"]}
        return None
    finally:
        cursor.close()
        db.close()


def create_user(pseudo, password, color, level=1, db_mode="local"):
    """Crée un utilisateur (bcrypt). Lève ValueError si pseudo existe déjà."""
    pseudo = (pseudo or "").strip()
    if not pseudo:
        raise ValueError("Pseudo requis")

    exists = fetch_all("SELECT id FROM users WHERE pseudo=%s", (pseudo,), db_mode)
    if exists:
        raise ValueError("Ce pseudo existe déjà")

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    db = get_connection(db_mode)
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (pseudo, hash, level, color) VALUES (%s, %s, %s, %s)",
            (pseudo, hashed, level, color),
        )
        db.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        db.close()

