from flask import Flask

app = Flask(__name__)

@app.route('/')
def inicio():
    return "<h1>Bienvenido a Taller Python Web: Mi Lista de Tareas</h1><p>El servidor está funcionando correctamente.</p>"

@app.route('/hola/<nombre>')
def hola(nombre):
    return f"Hola <strong>{nombre}</strong>, prepárate para organizar tus tareas de hoy."

if __name__ == '__main__':
    app.run(debug=True, port=5000)