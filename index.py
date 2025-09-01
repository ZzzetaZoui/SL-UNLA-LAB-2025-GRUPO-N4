from fastapi import FastAPI
app = FastAPI()
@app.get("/hola-mundo")
def hola_mundo():
    return "Hello World!"
#APARTADO PARA REGISTER

#APARTADO DE LOGIN

#APARTADO PARA CORROBORAR SI ESTAMOS HABILITADOS PARA OBTENER UN TURNO