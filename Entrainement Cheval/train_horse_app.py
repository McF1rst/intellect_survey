import streamlit as st
import pandas as pd
import os
import datetime

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

# Chemin vers le fichier Excel
file_path = "tableau histoire.xlsx"

# Charger les données
if os.path.exists(file_path):
    df = pd.read_excel(file_path)

    # Assurer que la colonne 'Date' est bien en datetime.date
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
else:
    st.error("Le fichier Excel n'existe pas.")
    st.stop()

# Date du jour
today_date = datetime.datetime.now().date()

# Si la date du jour est dans le tableau, l’utiliser comme sélection par défaut
if today_date in df["Date"].values:
    default_index = df[df["Date"] == today_date].index[0]
else:
    default_index = 0  # Si la date du jour n'est pas dans le tableau, prendre la première

# Liste des dates disponibles
date_options = df["Date"].tolist()

# Menu déroulant dans la sidebar
selected_date = st.sidebar.selectbox(
    "Choisir une date de séance",
    options=date_options,
    index=default_index,
    format_func=lambda x: x.strftime("%A %d %B %Y")  # Format lisible
)

# Récupérer la ligne correspondant à la date sélectionnée
row_index = df[df["Date"] == selected_date].index[0]
row = df.loc[row_index]

# Interface principale
st.subheader(f"Séance du {format_date_fr(selected_date)}")
st.write(f"**Exercice :** {row['Séance']}")

# Observation
observation = st.text_area("Observation santé", value=row.get("Observation santé", ""))
col1, col2 = st.columns(2)
with col1:
    poids = st.text_area("Poids", value = row.get("Poid", ""))
with col2:
    pieds = st.text_area("Pieds", value = row.get("Pieds", ""))
with col1:
    is_ok = st.checkbox("Marquer la séance comme terminée")
# Mettre à jour le DataFrame
df.at[row_index, "Observation santé"] = observation
df.at[row_index, "Poid"] = poids
df.at[row_index, "Pieds"] = pieds

df.at[row_index, "ok"] = is_ok

# Bouton d'enregistrement
if st.button("Enregistrer les modifications"):
    df.to_excel(file_path, index=False)
    st.success("Modifications enregistrées avec succès.")
