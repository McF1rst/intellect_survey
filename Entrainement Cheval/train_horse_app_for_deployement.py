import streamlit as st
import gspread
from google.oauth2 import service_account
import pandas as pd
import datetime
import hashlib

# --- Authentification simple ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Récupérer les utilisateurs depuis st.secrets
user_passwords = {user: hash_password(pwd) for user, pwd in st.secrets['users'].items()}

def login():
    st.title('Connexion')
    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type='password')
    if st.button('Se connecter'):
        if username in user_passwords and user_passwords[username] == hash_password(password):
            st.session_state['logged_in'] = True
            st.session_state['user'] = username
            st.rerun()
        else:
            st.error("Nom d'utilisateur ou mot de passe incorrect.")

# Gérer la session utilisateur
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if not st.session_state['logged_in']:
    login()
    st.stop()

# Authentification Google Sheets
dict_secrets = dict(st.secrets['gcp_service_account'])
dict_secrets['private_key'] = dict_secrets['private_key'].replace('\\n','\n')
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
]
creds = service_account.Credentials.from_service_account_info(dict_secrets, scopes=scopes)
client = gspread.authorize(creds)

# Accès à la feuille
SHEET_ID = '140J6nu7r_vcJRHMRmCZEr_2lLD49S5pYZTLA1QmPhis'
gsheet = client.open_by_key(SHEET_ID).sheet1

# Lecture des données
records = gsheet.get_all_records()
df = pd.DataFrame(records)
df['Date'] = pd.to_datetime(df['Date']).dt.date

# Dictionnaires pour format français
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

# Navigation entre pages
pages = ['Voir séances', 'Gérer séances']
page = st.sidebar.radio('Navigation', pages)

if page == 'Gérer séances':
    st.title('Ajouter ou supprimer une séance')
    # Ajout de séance
    st.info('### Ajouter une séance')
    col1, col2 = st.columns(2)
    with col1:
        new_date = st.date_input('Date de la nouvelle séance', value=datetime.date.today())
    with col2:
        new_exercise = st.text_input("Exercice associé", value="")
    if st.button('Ajouter cette séance'):
        if new_date in df['Date'].values:
            st.warning('Cette date existe déjà. Si vous voulez la modifier, supprimez-la puis recréez la.')
        else:
            new_row = {col: '' for col in df.columns if col!='Séance'}
            new_row['Date'] = new_date
            new_row['Séance'] = new_exercise
            values = [str(new_row[col]) for col in list(new_row.keys())]
            gsheet.append_row(values)
            st.success('Nouvelle séance ajoutée avec succès.')
            # st.rerun()

    st.markdown('---')
    # Suppression de séance
    st.info('### Supprimer une séance')
    del_date = st.date_input('Date de la séance à supprimer')
    if st.button('Supprimer cette séance'):
        if del_date not in df['Date'].values:
            st.warning('Aucune séance pour cette date.')
        else:
            # Calcul de l'index dans la feuille (1-based + header)
            raw_index = df[df['Date'] == del_date].index[0]
            row_index = int(raw_index) + 2  # Cast to native int for JSON serialization
            try:
                # Utiliser delete_rows (gspread v5+)
                gsheet.delete_rows(row_index)
                st.success('Séance supprimée avec succès.')
                # st.rerun()
            except AttributeError:
                # Fallback : effacer la ligne (remplacer par cellules vides)
                num_cols = len(df.columns)
                blank = [''] * num_cols
                end_col = chr(65 + num_cols - 1)
                gsheet.update(f'A{row_index}:{end_col}{row_index}', [blank])
                st.success('Séance effacée (remplacement par vide).')
                # st.rerun()

elif page == 'Voir séances':
    st.subheader('Consultation et mise à jour des séances')
    # Sélection de la date
    today = datetime.datetime.now().date()
    default_idx = int(df[df['Date'] == today].index[0]) if today in df['Date'].values else 0
    selected_date = st.sidebar.selectbox(
        'Choisir une date de séance', options=df['Date'].tolist(),
        index=default_idx, format_func=format_date_fr
    )
    row_idx = df[df['Date'] == selected_date].index[0]
    row = df.loc[row_idx]
    st.subheader(f"Séance du {format_date_fr(selected_date)}")
    st.write(f"**Exercice :** {row.get('Séance','')}")

    # Champs de saisie
    obs = st.text_area('Observation santé', value=row.get('Observation santé',''))
    col1, col2 = st.columns(2)
    with col1:
        poids = st.text_input('Poids', value=row.get('Poid',''))
    with col2:
        pieds = st.text_input('Pieds', value=row.get('Pieds',''))
    with col1:
        is_ok = st.checkbox('Marquer la séance comme terminée', value=row.get('ok', False))

    # Mise à jour du DF
    df.at[row_idx, 'Observation santé'] = obs
    df.at[row_idx, 'Poid'] = poids
    df.at[row_idx, 'Pieds'] = pieds
    df.at[row_idx, 'ok'] = is_ok

    if st.button('Enregistrer les modifications'):
        df_up = df.copy()
        import numpy as np
        df_up.replace([np.inf, -np.inf], np.nan, inplace=True)
        df_up = df_up.where(pd.notnull(df_up), None)
        for col in df_up.columns:
            if pd.api.types.is_datetime64_any_dtype(df_up[col]) or df_up[col].apply(lambda x: isinstance(x, datetime.date)).any():
                df_up[col] = df_up[col].astype(str)
        gsheet.update([df_up.columns.tolist()] + df_up.values.tolist())
        st.success('Modifications enregistrées avec succès.')
