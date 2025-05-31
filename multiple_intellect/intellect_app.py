import streamlit as st
from questions import questions
import plotly.graph_objects as go
import plotly.io as pio
from io import BytesIO


st.set_page_config(page_title="Intelligences Multiples", layout="centered")

# Liste des pages (intelligences + résultats)
pages = list(questions.keys()) + ["🧾 Résultats"]

# Initialisation de l'état
if "results" not in st.session_state:
    st.session_state["results"] = {key: 0 for key in questions.keys()}
if "page_index" not in st.session_state:
    st.session_state["page_index"] = 0

# Réinitialisation de tout
def reset_form():
    st.session_state["results"] = {key: 0 for key in questions.keys()}
    st.session_state["page_index"] = 0
    for key in list(st.session_state.keys()):
        if key not in ("results", "page_index"):
            del st.session_state[key]

# Page en cours
selected_page = pages[st.session_state["page_index"]]

st.title("🧠 Test des Intelligences Multiples")

# 📋 Affichage d'une page de question
if selected_page in questions:
    st.header(selected_page)

    score = 0
    for q in questions[selected_page]:
        if st.checkbox(q, key=q):
            score += 1

    st.session_state["results"][selected_page] = score
    st.write(f"✅ Score pour **{selected_page}** : **{score}/10**")

    # ➡️ Bouton pour aller à la page suivante
    if st.session_state["page_index"] < len(pages) - 1:
        next_page = pages[st.session_state["page_index"] + 1]
        if st.button(f"➡️ Continuer vers {next_page}"):
            st.session_state["page_index"] += 1
            st.rerun()

# 📊 Page des résultats
elif selected_page == "🧾 Résultats":
    st.subheader("🎯 Résumé de vos scores")
    scores = st.session_state["results"]

    for k, v in scores.items():
        st.write(f"**{k}** : {v}/10")

    labels = list(scores.keys())
    values = list(scores.values())
    labels += [labels[0]]
    values += [values[0]]

    fig = go.Figure(
        data=go.Scatterpolar(
            r=values,
            theta=labels,
            fill='toself',
            name='Scores',
            line_color='dodgerblue'
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
        showlegend=False,
        title="Polygone d’intelligences multiples"
    )
    col1, col2 = st.columns(2)

    # Génération de l'image du graphique pour export
    buffer = BytesIO()
    pio.write_image(fig, buffer, format="pdf")  # nécessite kaleido
    buffer.seek(0)

    st.plotly_chart(fig)
    # Bouton de téléchargement
    with col1:
        st.download_button(
            label="📥 Télécharger le graphique en PDF",
            data=buffer,
            file_name="intelligences_multiples.pdf",
            mime="application/pdf"
        )

    with col2:
        if st.button("🔄 Recommencer le test"):
            reset_form()
            st.rerun()
