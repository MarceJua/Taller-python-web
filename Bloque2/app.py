from flask import Flask, render_template, request

app = Flask(__name__)

tareas_ficticias = ["Comprar medicina", "Hacer ejercicio", "Leer 20 mins"]

@app.route('/')
def inicio():
    return render_template('index.html', usuario="Estudiante USAC")

@app.route('/tareas')
def ver_tareas():
    return render_template('tareas.html', lista=tareas_ficticias)

@app.route('/saludo', methods=['POST'])
def saludo_post():
    nombre = request.form.get('nombre_usuario')
    return render_template('index.html', usuario=nombre)

if __name__ == '__main__':
    app.run(debug=True, port=5000)