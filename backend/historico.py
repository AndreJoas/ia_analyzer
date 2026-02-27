# backend/historico.py
from flask import Blueprint, jsonify, session
import sqlite3
from backend.config import DB_PATH

from backend.config import app

@app.route('/historico', methods=['GET'])
def historico():
    user_id = session.get("user", {}).get("id")
    if not user_id:
        return jsonify([])

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, score, sugestoes, data FROM analises WHERE user_id=? ORDER BY data DESC', (user_id,))
    rows = c.fetchall()
    conn.close()

    return jsonify([
        {
            'id': row[0],
            'score': row[1],
            'sugestoes': row[2],
            'data': row[3]
        }
        for row in rows
    ])