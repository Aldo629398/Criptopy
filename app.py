import io
import zipfile
from flask import Flask, render_template, request, send_file, jsonify, flash, redirect, url_for
from crypto_utils import encrypt_bytes, decrypt_bytes, generate_strong_password

app = Flask(__name__)
app.secret_key = "cambia_esta_clave_secreta_en_produccion"

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/generate-password", methods=["GET"])
def api_generate_password():
    length = request.args.get("length", default=20, type=int)
    length = max(12, min(length, 64))
    return jsonify({"password": generate_strong_password(length)})

@app.route("/encrypt", methods=["POST"])
def encrypt_folder():
    files = request.files.getlist("folder_files")
    password = request.form.get("password", "")

    if not files or files[0].filename == "":
        flash("Selecciona una carpeta válida.", "error")
        return redirect(url_for("index"))

    if len(password) < 8:
        flash("La contraseña debe tener al menos 8 caracteres.", "error")
        return redirect(url_for("index"))

    # Empaquetar toda la carpeta en un ZIP en memoria preservando rutas
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in files:
            # file.filename contiene la ruta relativa (ej. "MiCarpeta/fotos/img.jpg")
            if file.filename:
                zf.writestr(file.filename, file.read())

    zip_buffer.seek(0)
    encrypted_data = encrypt_bytes(zip_buffer.read(), password)

    # Obtener nombre base de la carpeta
    root_folder = files[0].filename.split("/")[0] or "carpeta_cifrada"

    return send_file(
        io.BytesIO(encrypted_data),
        as_attachment=True,
        download_name=f"{root_folder}.vault",
        mimetype="application/octet-stream"
    )

@app.route("/decrypt", methods=["POST"])
def decrypt_folder():
    vault_file = request.files.get("vault_file")
    password = request.form.get("password", "")

    if not vault_file or vault_file.filename == "":
        flash("Sube un archivo .vault para descifrar.", "error")
        return redirect(url_for("index"))

    try:
        decrypted_zip = decrypt_bytes(vault_file.read(), password)
    except Exception:
        flash("Contraseña incorrecta o archivo dañado.", "error")
        return redirect(url_for("index"))

    original_name = vault_file.filename.rsplit(".", 1)[0] + "_descifrado.zip"

    return send_file(
        io.BytesIO(decrypted_zip),
        as_attachment=True,
        download_name=original_name,
        mimetype="application/zip"
    )

if __name__ == "__main__":
    app.run(debug=True)