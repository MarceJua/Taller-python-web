import os
from datetime import datetime, timezone

from bson.errors import InvalidId
from bson.objectid import ObjectId
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from pymongo import MongoClient

load_dotenv()

app = Flask(__name__)

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "todo_db")

if not MONGO_URI:
    raise RuntimeError("Falta MONGO_URI en las variables de entorno.")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
tasks = db.Tareas


def serialize_task(task):
    return {
        "id": str(task["_id"]),
        "title": task.get("title", ""),
        "description": task.get("description", ""),
        "done": task.get("done", False),
        "created_at": task.get("created_at").isoformat() if task.get("created_at") else None,
        "updated_at": task.get("updated_at").isoformat() if task.get("updated_at") else None,
    }


def get_task_or_404(task_id):
    try:
        obj_id = ObjectId(task_id)
    except (InvalidId, TypeError):
        return None, (jsonify({"error": "ID inválido"}), 400)

    task = tasks.find_one({"_id": obj_id})
    if not task:
        return None, (jsonify({"error": "Tarea no encontrada"}), 404)

    return task, None

# Obtiene todas las tareas
@app.get("/api/tareas")
def get_tasks():
    all_tasks = list(tasks.find().sort("created_at", -1))
    return jsonify([serialize_task(task) for task in all_tasks]), 200

# Obtiene una tarea por su ID
@app.get("/api/tareas/<id_tarea>")
def get_task(id_tarea):
    task, error = get_task_or_404(id_tarea)
    if error:
        return error
    return jsonify(serialize_task(task)), 200

# Crea una nueva tarea
@app.post("/api/tareas")
def create_task():
    data = request.get_json(silent=True) or {}

    title = str(data.get("title", "")).strip()
    description = str(data.get("description", "")).strip()

    if not title:
        return jsonify({"error": "El campo 'title' es obligatorio"}), 400

    now = datetime.now(timezone.utc)

    result = tasks.insert_one({
        "title": title,
        "description": description,
        "done": False,
        "created_at": now,
        "updated_at": now,
    })

    created_task = tasks.find_one({"_id": result.inserted_id})
    return jsonify(serialize_task(created_task)), 201

# Modifica los datos de una tarea existente
@app.put("/api/tareas/<id_tarea>")
def update_task(id_tarea):
    task, error = get_task_or_404(id_tarea)
    if error:
        return error

    data = request.get_json(silent=True) or {}

    title = str(data.get("title", task.get("title", ""))).strip()
    description = str(data.get("description", task.get("description", ""))).strip()
    done = bool(data.get("done", task.get("done", False)))

    if not title:
        return jsonify({"error": "El campo 'title' no puede estar vacío"}), 400

    now = datetime.now(timezone.utc)

    tasks.update_one(
        {"_id": ObjectId(id_tarea)},
        {"$set": {
            "title": title,
            "description": description,
            "done": done,
            "updated_at": now,
        }},
    )

    updated_task = tasks.find_one({"_id": ObjectId(id_tarea)})
    return jsonify(serialize_task(updated_task)), 200

# Cambia el estado de una tarea
@app.patch("/api/tareas/<id_tarea>/toggle")
def toggle_task(id_tarea):
    task, error = get_task_or_404(id_tarea)
    if error:
        return error

    new_done = not task.get("done", False)
    now = datetime.now(timezone.utc)

    tasks.update_one(
        {"_id": ObjectId(id_tarea)},
        {"$set": {
            "done": new_done,
            "updated_at": now,
        }},
    )

    updated_task = tasks.find_one({"_id": ObjectId(id_tarea)})
    return jsonify(serialize_task(updated_task)), 200

# Borra una tarea por su ID
@app.delete("/api/tareas/<id_tarea>")
def delete_task(id_tarea):
    try:
        obj_id = ObjectId(id_tarea)
    except (InvalidId, TypeError):
        return jsonify({"error": "ID inválido"}), 400

    result = tasks.delete_one({"_id": obj_id})

    if result.deleted_count == 0:
        return jsonify({"error": "Tarea no encontrada"}), 404

    return jsonify({"message": "Tarea eliminada correctamente"}), 200


if __name__ == "__main__":
    app.run(debug=True)