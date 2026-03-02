import streamlit as st
import pickle
import pandas as pd
import requests
from dotenv import load_dotenv
import os

#  1. CONFIGURATION
st.set_page_config(page_title="Movie Recommender", layout="wide", page_icon="🎬")

# A. Gestion de la liste de favoris
if 'favorites' not in st.session_state:
    st.session_state['favorites'] = []

# B. Gestion des résultats de recherche
if 'recommendations' not in st.session_state:
    st.session_state['recommendations'] = None


def toggle_favorite(movie_name):
    if movie_name in st.session_state['favorites']:
        st.session_state['favorites'].remove(movie_name)
    else:
        st.session_state['favorites'].append(movie_name)


# 2. FENÊTRE POP-UP (WATCHLIST)
@st.dialog("Ma Watchlist")
def show_watchlist_dialog():
    st.caption("Vos films sauvegardés")
    st.write("---")

    if st.session_state['favorites']:
        for fav in st.session_state['favorites']:
            col_txt, col_del = st.columns([4, 1])
            with col_txt:
                st.write(f" *{fav}*")
            with col_del:
                if st.button("❌", key=f"del_{fav}"):
                    toggle_favorite(fav)
                    st.rerun()

        st.write("---")
        if st.button("🗑️ Tout effacer", type="primary"):
            st.session_state['favorites'] = []
            st.rerun()
    else:
        st.info("Votre liste est vide.")
        if st.button("Fermer"):
            st.rerun()


# 3. CHARGEMENT DONNÉES
@st.cache_data
def load_movies():
    try:
        movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
        return pd.DataFrame(movies_dict)
    except FileNotFoundError:
        return pd.DataFrame()


@st.cache_resource
def load_similarity():
    try:
        return pickle.load(open('similarity.pkl', 'rb'))
    except FileNotFoundError:
        return None


movies = load_movies()
similarity = load_similarity()

if movies.empty or similarity is None:
    st.error("ERREUR : Fichiers manquants (movie_dict.pkl ou similarity.pkl).")
    st.stop()

load_dotenv()
#  4. API
def fetch_data(movie_id):
    api_key = os.getenv("API_KEY")
    url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-EN'
    placeholder = "https://via.placeholder.com/500x750/1a1a1a/ffffff?text=No+Image"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        poster = "https://image.tmdb.org/t/p/w500" + data['poster_path'] if data.get('poster_path') else placeholder
        overview = data.get('overview', "Pas de description disponible.")
        return poster, overview
    except:
        return placeholder, "Pas de description disponible."


#5. ALGO
def recommend(movie):
    try:
        movie_index = movies[movies['title'] == movie].index[0]
        distances = similarity[movie_index]
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

        rec_data = []
        for i in movies_list:
            item_id = movies.iloc[i[0]].movie_id
            title = movies.iloc[i[0]].title
            score = round(i[1] * 100, 1)
            poster, overview = fetch_data(item_id)

            rec_data.append({
                "title": title,
                "poster": poster,
                "overview": overview,
                "score": score
            })
        return rec_data
    except Exception:
        return []


#  6. CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;500;700&display=swap');

    /* BACKGROUND */
    .stApp::before {
        content: ""; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background-image: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.9)), 
                          url('https://assets.nflxext.com/ffe/siteui/vlv3/f841d4c7-10e1-40af-bcae-07a3f8dc141a/f6d7434e-d6de-4185-a6d4-c77a2d08737b/US-en-20220502-popsignuptwoweeks-perspective_alpha_website_medium.jpg');
        background-size: cover; background-position: center; filter: blur(10px); transform: scale(1.1); z-index: -1;
    }
    .stApp { background-color: transparent; color: white; font-family: 'Outfit', sans-serif; }

    /* HIDE HEADER */
    header {visibility: hidden;}
    [data-testid="stHeader"] { background-color: transparent; }
    .block-container { padding-top: 2rem; }

    /* TITRES */
    .main-title {
        font-size: 4rem; font-weight: 700; text-align: center; margin: 10px 0;
        background: linear-gradient(74deg, #4285F4 0%, #9B72CB 50%, #D96570 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .subtitle { color: #d1d1d1; text-align: center; margin-bottom: 30px; font-size: 1.2rem; }

    /* INPUTS & BOUTONS */
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: rgba(30, 31, 32, 0.9); border: 1px solid rgba(255, 255, 255, 0.2); color: white;
    }

    /* Bouton Principal (Recommander + Menu) */
    div.stButton > button {
        background: linear-gradient(90deg, #2b3952 0%, #29304a 100%); color: white; 
        border: 1px solid rgba(255,255,255,0.1); height: 48px;
    }
    div.stButton > button:hover {
        background: linear-gradient(90deg, #4285F4 0%, #9B72CB 100%); border: none;
    }

    /* CARTE FILM */
    .movie-card {
        background-color: rgba(30, 31, 32, 0.7); backdrop-filter: blur(10px);
        padding: 10px; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center; height: 100%; transition: transform 0.3s;
    }
    .movie-card:hover { transform: translateY(-5px); border: 1px solid rgba(155, 114, 203, 0.5); }
    .movie-card img { width: 100%; border-radius: 12px; aspect-ratio: 2/3; object-fit: cover; margin-bottom: 8px; }
    /* --- REMPLACE CETTE PARTIE DANS TON CSS --- */

    [data-testid="stPopover"] button {
        background-color: rgba(30, 31, 32, 0.8) !important; /* Sombre */
        color: #e0e0e0 !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        backdrop-filter: blur(10px);
        border-radius: 12px !important;
        width: 100%;
        margin-top: 5px;
    }
    [data-testid="stPopover"] button:hover {
        transform: translateY(-4px); border: 1px solid rgba(155, 114, 203, 0.5)
    }

</style>
""", unsafe_allow_html=True)

#  7. INTERFACE PRINCIPALE

st.markdown('<h1 class="main-title">Hello Movie Lover </h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Let AI find your next favorite movie</p>', unsafe_allow_html=True)

# Structure : [Espace(1), Menu(2), Recherche(5), Bouton(2), Espace(1)]
# Cela crée une symétrie parfaite et centre le tout.
c_pad1, c_menu, c_search, c_btn, c_pad2 = st.columns([1, 2, 5, 2, 1], gap="small")

# 1. Bouton LISTE
with c_menu:
    if st.button("☰ My Liste", use_container_width=True):
        show_watchlist_dialog()

# 2. Barre de recherche
with c_search:
    selected_movie_name = st.selectbox(
        "Film", movies['title'].values,
        label_visibility="collapsed", placeholder="Rechercher..."
    )

# 3. Bouton Recommander
with c_btn:
    clicked = st.button("Recommande", use_container_width=True)

# Logique
if clicked:
    with st.spinner('Thinking...'):
        st.session_state['recommendations'] = recommend(selected_movie_name)

st.write("---")

#  8. RÉSULTATS

if st.session_state['recommendations']:
    rec_data = st.session_state['recommendations']
    cols = st.columns(5, gap="small")

    for i, col in enumerate(cols):
        movie = rec_data[i]
        with col:
            color = "#28a745" if movie['score'] >= 60 else "#ffc107"
            st.markdown(f"""
                <div class="movie-card">
                    <img src="{movie['poster']}">
                    <div style="margin-bottom:5px;">
                        <span style="background-color:{color};padding:4px 8px;border-radius:12px;font-size:0.75rem;font-weight:bold;color:white;">{movie['score']}% Match</span>
                    </div>
                    <p style="font-weight:500;margin-bottom:5px;">{movie['title']}</p>
                </div>
                """, unsafe_allow_html=True)

            with st.container():
                with st.popover("Description", use_container_width=True):
                    st.markdown(f"### {movie['title']}")
                    st.write(movie['overview'])

                is_fav = movie['title'] in st.session_state['favorites']
                if st.button("Retirer" if is_fav else "Ma Liste", key=f"btn_{i}",
                             type="primary" if is_fav else "secondary", use_container_width=True):
                    toggle_favorite(movie['title'])
                    st.rerun()