import re
import fitz  # PyMuPDF
import pandas as pd
from flask import Flask, render_template, request, send_file
from io import BytesIO

app = Flask(__name__)

# Expresión regular para extraer la información relevante del PDF
patron = re.compile(r"^(\d{12})\s+.*?\s+(\d{2}-\d{8}-\d)(.*)")  

def extraer_y_generar_csv(file_stream):
    """Extrae texto de un PDF subido en memoria y devuelve un CSV en memoria."""
    
    datos = []
    
    with fitz.open("pdf", file_stream.read()) as doc:  # Abrimos el PDF en memoria
        for pagina in doc:
            bloques = pagina.get_text("blocks")  # Extraemos bloques de texto
            for bloque in bloques:
                texto = bloque[4].strip().replace("\n", " ")  # Limpiamos el texto
                
                match = patron.match(texto)
                if match:
                    texto_limpio = f"{match.group(1)};{match.group(2)}{match.group(3)}"
                    texto_limpio = re.sub(r"\s+", ";", texto_limpio)  
                    columnas = texto_limpio.split(";")[:6]  
                    
                    if len(columnas) == 6:
                        columnas[0] = "S" + columnas[0]  # Agregar "S" al inicio del valor en la primera columna
                        datos.append(columnas)

    # Convertimos los datos extraídos en un DataFrame
    df = pd.DataFrame(datos, columns=["Asociado", "CUIL", "Plan", "Cantidad", "MontoComprometido", "AportedeLey"])
    
    # Guardamos el DataFrame en un buffer de memoria
    output = BytesIO()
    df.to_csv(output, index=False, sep=";")
    output.seek(0)  # Nos aseguramos de que el puntero está al inicio del archivo
    
    return output

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Recibe un PDF, lo procesa y devuelve un CSV como respuesta de descarga."""
    
    if 'file' not in request.files:
        return "No se ha enviado ningún archivo"

    file = request.files['file']

    if file.filename == '':
        return "No se seleccionó ningún archivo"

    if file and file.filename.lower().endswith(".pdf"):
        csv_output = extraer_y_generar_csv(file)
        return send_file(csv_output, mimetype="text/csv", as_attachment=True, download_name="resultado.csv")

    return "Tipo de archivo no permitido"

if __name__ == '__main__':
    app.run(debug=True)
