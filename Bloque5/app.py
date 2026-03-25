import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from bson.codec_options import CodecOptions
from bson.objectid import ObjectId
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from pymongo import MongoClient

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

if not MONGO_URI:
    raise RuntimeError("Falta MONGO_URI en las variables de entorno.")

client = MongoClient(MONGO_URI)

local_tz = ZoneInfo("America/Guatemala")
codec_options = CodecOptions(tz_aware=True, tzinfo=local_tz)

db = client[DB_NAME]
tasks = db.get_collection("Tareas", codec_options=codec_options)

@app.template_filter("datetime_local")
def datetime_local(value):
    if not value:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    return str(value)


def parse_bool(value):
    return str(value).lower() in {"1", "true", "on", "yes"}


@app.route("/")
def index():
    all_tasks = list(tasks.find().sort("created_at", -1))
    return render_template("index.html", tasks=all_tasks)


@app.route("/add", methods=["POST"])
def add_task():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()

    if not title:
        flash("El título de la tarea es obligatorio.", "danger")
        return redirect(url_for("index"))

    tasks.insert_one({
        "title": title,
        "description": description,
        "done": False,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    })

    flash("Tarea creada correctamente.", "success")
    return redirect(url_for("index"))


@app.route("/toggle/<task_id>", methods=["POST"])
def toggle_task(task_id):
    task = tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        flash("La tarea no existe.", "warning")
        return redirect(url_for("index"))

    tasks.update_one(
        {"_id": ObjectId(task_id)},
        {"$set": {
            "done": not task.get("done", False),
            "updated_at": datetime.now(timezone.utc),
        }},
    )
    flash("Estado de la tarea actualizado.", "success")
    return redirect(url_for("index"))


@app.route("/edit/<task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    task = tasks.find_one({"_id": ObjectId(task_id)})
    if not task:
        flash("La tarea no existe.", "warning")
        return redirect(url_for("index"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        done = parse_bool(request.form.get("done"))

        if not title:
            flash("El título no puede estar vacío.", "danger")
            return redirect(url_for("edit_task", task_id=task_id))

        tasks.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {
                "title": title,
                "description": description,
                "done": done,
                "updated_at": datetime.now(timezone.utc),
            }},
        )
        flash("Tarea actualizada correctamente.", "success")
        return redirect(url_for("index"))

    return render_template("edit.html", task=task)


@app.route("/delete/<task_id>", methods=["POST"])
def delete_task(task_id):
    result = tasks.delete_one({"_id": ObjectId(task_id)})
    if result.deleted_count == 0:
        flash("No se pudo eliminar la tarea.", "warning")
    else:
        flash("Tarea eliminada correctamente.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
