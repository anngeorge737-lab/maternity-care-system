MATERNITY CARE INFORMATION SYSTEM — WEB VERSION

Files:
- app.py: Flask web application
- templates/: browser pages
- static/style.css: responsive styling
- requirements.txt: Python dependencies
- Procfile: deployment start command

For online deployment:
1. Upload these files to a GitHub repository.
2. Create a new Web Service on Render and connect that repository.
3. Build command: pip install -r requirements.txt
4. Start command: gunicorn app:app
5. Add a persistent disk and set DATABASE_PATH to a file on that disk if you want records to persist across redeployments.
6. Set SECRET_KEY to a long random value.

IMPORTANT:
This is a school-project prototype, not a production-ready medical records system.
Do not enter real patient information until you add login/access controls, secure hosting, backups, HTTPS, audit logs, and appropriate privacy protections. SQLite storage on free hosting may not persist unless configured with persistent storage.
