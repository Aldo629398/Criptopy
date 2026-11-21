# Bóveda de Carpetas — Cifrado Web con Flask, Argon2id y AES-256-GCM

Aplicación web desarrollada en **Python 3** y **Flask** que permite cifrar y descifrar carpetas completas (incluyendo subdirectorios y cualquier tipo de archivo: documentos de Office, imágenes, videos, texto plano o código fuente) mediante algoritmos criptográficos modernos y autenticados.

---

## Características Principales

* **Soporte agnóstico al formato de archivo:** Procesa cualquier tipo de archivo a nivel binario (`bytes`) sin alterar su contenido original.
* **Preservación de estructura de directorios:** Empaqueta la carpeta seleccionada en un contenedor ZIP en memoria antes del cifrado, manteniendo las rutas relativas de archivos y subcarpetas, y ocultando los nombres y tamaños individuales dentro del archivo cifrado resultante (`.vault`).
* **Criptografía moderna:**
  * Derivación de claves resistente a ataques de fuerza bruta y hardware especializado mediante **Argon2id**.
  * Cifrado autenticado mediante **AES-256-GCM**, garantizando confidencialidad e integridad de los datos.
* **Generador de contraseñas seguras:** Endpoint integrado que genera contraseñas aleatorias de alta entropía utilizando el módulo criptográfico `secrets` de Python, además de permitir contraseñas personalizadas.

---

## Arquitectura Criptográfica

El sistema implementa un esquema de cifrado simétrico basado en contraseña (*Password-Based Encryption*) siguiendo las recomendaciones actuales de OWASP:

### 1. Derivación de Clave (`Argon2id`)
A partir de la contraseña ingresada por el usuario y una sal (*salt*) aleatoria única por operación, se deriva una llave simétrica de **256 bits (32 bytes)** con los siguientes parámetros:
* **Variante:** `Argon2id` (híbrido resistente a ataques de canal lateral y GPU/ASIC).
* **Salt:** $16\text{ bytes}$ ($128\text{ bits}$) generados con `os.urandom(16)`.
* **Costo de tiempo (`time_cost`):** $3$ iteraciones.
* **Costo de memoria (`memory_cost`):** $65\,536\text{ KiB}$ ($64\text{ MB}$ de RAM por derivación).
* **Paralelismo (`parallelism`):** $4$ hilos.
* **Longitud de llave (`hash_len`):** $32\text{ bytes}$ ($256\text{ bits}$).

### 2. Cifrado Autenticado (`AES-256-GCM`)
El flujo de bytes del archivo ZIP empaquetado se cifra utilizando **AES en modo Galois/Counter Mode (GCM)**:
* **Nonce / IV:** $12\text{ bytes}$ ($96\text{ bits}$) generados aleatoriamente con `os.urandom(12)`.
* **Etiqueta de autenticación (Tag):** $16\text{ bytes}$ ($128\text{ bits}$). Si la contraseña es incorrecta o algún byte del archivo `.vault` fue modificado, la verificación falla (`InvalidTag`) y se rechaza el descifrado.

### 3. Estructura Binaria del Archivo `.vault`

Cada archivo generado tiene la siguiente estructura secuencial en bytes:

```text
+-------------------+--------------------+---------------------------------------+
|   SALT (16 B)     |    NONCE (12 B)    |      CIPHERTEXT + GCM TAG (N B)       |
+-------------------+--------------------+---------------------------------------+
0                  16                   28                                     Final
```

---

## Estructura del Proyecto

```text
cifrado/
├── app.py               # Servidor Flask, rutas HTTP y empaquetado ZIP en memoria
├── crypto_utils.py      # Funciones criptográficas (Argon2id, AES-256-GCM y generador)
├── requirements.txt     # Dependencias del proyecto
├── README.md            # Documentación técnica
└── templates/
    └── index.html         # Interfaz web con selección de carpetas (webkitdirectory)
```

---

## Requisitos e Instalación Local

### Requisitos Previos
* **Python 3.10** o superior.
* Soporte para entornos virtuales (`python3-venv` en sistemas Debian/Ubuntu/Kali).

### Pasos de Instalación

1. **Clonar o ubicarse en el directorio del proyecto:**
   ```bash
   cd /ruta/al/proyecto/cifrado
   ```

2. **Crear y activar un entorno virtual aislado:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
   *(En Windows PowerShell: `.\.venv\Scripts\Activate.ps1`)*

3. **Instalar las dependencias:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

   Contenido de `requirements.txt`:
   ```text
   Flask==3.1.0
   cryptography==44.0.0
   argon2-cffi==23.1.0
   gunicorn==23.0.0
   ```

4. **Ejecutar la aplicación en modo local:**
   ```bash
   python app.py
   ```
   La aplicación estará disponible en `http://127.0.0.1:5000`.

---

## Referencia de Endpoints (API / Rutas)

| Método | Ruta | Descripción | Parámetros / Cuerpo | Respuesta |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Renderiza la interfaz web principal. | Ninguno | HTML (`index.html`) |
| `GET` | `/generate-password` | Genera una contraseña segura aleatoria. | `length` (Query, opcional, `12`–`64`, por defecto `20`) | JSON: `{"password": "..."}` |
| `POST` | `/encrypt` | Comprime y cifra los archivos de una carpeta. | `folder_files` (Archivos), `password` (mín. 8 caracteres) | Descarga binaria (`<carpeta>.vault`) |
| `POST` | `/decrypt` | Verifica integridad y descifra un `.vault`. | `vault_file` (Archivo `.vault`), `password` | Descarga ZIP (`<nombre>_descifrado.zip`) |

---

## Despliegue en Producción (Render)

Para desplegar el servicio en plataformas PaaS gratuitas como **Render**:

1. **Configurar variables de entorno:**
   * `SECRET_KEY`: Cadena aleatoria larga para firmar las sesiones y mensajes flash de Flask.
2. **Comandos de construcción y arranque:**
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `gunicorn app:app`

---

## Consideraciones de Seguridad y Rendimiento

* **Transporte cifrado (HTTPS):** En entornos fuera de `localhost`, es obligatorio servir la aplicación mediante **HTTPS** para proteger la contraseña durante su envío del navegador al servidor.
* **Uso de memoria RAM:** El procesamiento actual utiliza `io.BytesIO()` en memoria RAM. En instancias gratuitas con $512\text{ MB}$ de RAM (como el plan Free de Render), se recomienda limitar las carpetas a un tamaño máximo aproximado de $50\text{ MB}$–$100\text{ MB}$. Para carpetas de varios gigabytes, se sugiere migrar a almacenamiento temporal en disco (`tempfile`) y cifrado por bloques (*streaming*).
* **Recuperación de datos:** Al no almacenarse contraseñas ni llaves maestras en el servidor, **si se pierde la contraseña utilizada para cifrar un archivo `.vault`, es matemáticamente imposible recuperar su contenido**.