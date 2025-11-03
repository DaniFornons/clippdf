# 📎 ClipPDF

**ClipPDF** is a lightweight web app built with **Django** that allows you to:
- **Attach files** inside a PDF  
- **Extract embedded files** from a PDF as a ZIP  
- **Switch languages** between Catalan, English, and Spanish

You can test it live at:  
**[https://clippdf.pythonanywhere.com](https://clippdf.pythonanywhere.com)**

---

## How to Deploy 

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/clippdf.git
cd clippdf
```

### 2. Create your `.env` file
Copy the example and customize it:
```bash
cp .env.example .env
```

Example `.env`:
```bash
SECRET_KEY=change-this-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1
LANGUAGE_CODE=ca
```

---

## Run with Docker

### 1. Build and start the containers
```bash
docker compose build
docker compose up -d
```

This will start two containers:
- **web** → Django + Gunicorn  
- **nginx** → Serves static files and proxies requests to Gunicorn

### 2. Access the app
Once the containers are running, open:  
[http://localhost](http://localhost)

### 3. Stop the containers
```bash
docker compose down
```

---

## Run without Docker

### 1. Create and activate a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the development server
```bash
python manage.py runserver
```

### 4. Access the app
Open your browser at:  
[http://localhost:8000](http://localhost:8000)

### 5. Stop the server
Press:
```bash
Ctrl + C
```

---
