import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account
import pandas as pd
import datetime
import hashlib

# --- Authentification simple ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Utilisateurs autorisés (tu peux en ajouter d'autres ici)
users = {
    "laurane": hash_password("cheval2025"),
    "admin": hash_password("admin123")
}

def login():
    st.title("Connexion")

    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        if username in users and users[username] == hash_password(password):
            st.session_state["logged_in"] = True
            st.session_state["user"] = username
            st.experimental_rerun()
        else:
            st.error("Nom d'utilisateur ou mot de passe incorrect.")

# Vérifier si l'utilisateur est connecté
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
    st.stop()

# Authentification Google Sheets
creds = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)
client = gspread.authorize(creds)

# Ouvrir le fichier Google Sheets
SHEET_ID = "140J6nu7r_vcJRHMRmCZEr_2lLD49S5pYZTLA1QmPhis"
sheet = client.open_by_key(SHEET_ID).sheet1

# Lire les données
data = sheet.get_all_records()
df = pd.DataFrame(data)

# S'assurer que les dates sont bien au format datetime.date
df["Date"] = pd.to_datetime(df["Date"]).dt.date

# Formatter les dates en français
jours_fr = {
    'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi',
    'Thursday': 'Jeudi', 'Friday': 'Vendredi', 'Saturday': 'Samedi', 'Sunday': 'Dimanche'
}
mois_fr = {
    1: 'janvier', 2: 'février', 3: 'mars', 4: 'avril', 5: 'mai', 6: 'juin',
    7: 'juillet', 8: 'août', 9: 'septembre', 10: 'octobre', 11: 'novembre', 12: 'décembre'
}
def format_date_fr(date_obj):
    jour = jours_fr[date_obj.strftime('%A')]
    mois = mois_fr[date_obj.month]
    return f"{jour} {date_obj.day} {mois} {date_obj.year}"

# Date actuelle
today_date = datetime.datetime.now().date()
if today_date in df["Date"].values:
    default_index = df[df["Date"] == today_date].index[0]
else:
    default_index = 0

# Sélection de la date
date_options = df["Date"].tolist()
selected_date = st.sidebar.selectbox(
    "Choisir une date de séance",
    options=date_options,
    index=default_index,
    format_func=format_date_fr
)

# Récupérer la ligne sélectionnée
row_index = df[df["Date"] == selected_date].index[0]
row = df.loc[row_index]

# Affichage
st.subheader(f"Séance du {format_date_fr(selected_date)}")
st.write(f"**Exercice :** {row['Séance']}")

observation = st.text_area("Observation santé", value=row.get("Observation santé", ""))
col1, col2 = st.columns(2)
with col1:
    poids = st.text_area("Poids", value=row.get("Poid", ""))
with col2:
    pieds = st.text_area("Pieds", value=row.get("Pieds", ""))
with col1:
    is_ok = st.checkbox("Marquer la séance comme terminée")

# Mise à jour du DataFrame
df.at[row_index, "Observation santé"] = observation
df.at[row_index, "Poid"] = poids
df.at[row_index, "Pieds"] = pieds
df.at[row_index, "ok"] = is_ok

# Écriture dans Google Sheets
if st.button("Enregistrer les modifications"):
    # Convertir les dates pour l'envoi JSON
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]) or df[col].apply(lambda x: isinstance(x, datetime.date)).any():
            df[col] = df[col].astype(str)

    # Mise à jour dans Google Sheets
    sheet.update([df.columns.values.tolist()] + df.values.tolist())
    st.success("Modifications enregistrées avec succès.")

