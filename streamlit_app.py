# streamlit_app.py
# Point d'entrée pour Streamlit Cloud
# Redirige vers le vrai dashboard

import runpy
runpy.run_path("dashboard/app.py", run_name="__main__")