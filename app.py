import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pytz
from streamlit_js_eval import get_geolocation

# --- 1. CONFIGURACIÓ DE LA PÀGINA ---
st.set_page_config(page_title="Outdoor", page_icon="🌲", layout="centered")

# --- 2. CSS EXTREM (COLORS I MIDES) ---
st.markdown("""
    <style>
    /* 1. Títol Centrat */
    h1 {
        text-align: center;
        margin-top: -20px;
    }

    /* 2. Estil base per a TOTS els botons (Gegants) */
    div.stButton > button {
        height: 90px;                 /* Molt alts */
        font-size: 30px !important;   /* Lletra gegant */
        font-weight: 900 !important;  /* Negreta */
        border-radius: 15px;          /* Cantonades rodones */
        border: none;
        width: 100%;                  /* Ocupar tot l'ample disponible */
        box-shadow: 0px 4px 6px rgba(0,0,0,0.2); /* Ombra suau */
    }

    /* 3. Botó ENTRADA (Verd) - El detectem perquè és tipus 'secondary' */
    button[kind="secondary"] {
        background-color: #2eb82e !important; /* Verd gespa fort */
        color: white !important;
    }
    button[kind="secondary"]:active {
        background-color: #248f24 !important; /* Verd fosc al clicar */
    }

    /* 4. Botó SORTIDA (Vermell) - El detectem perquè és tipus 'primary' */
    button[kind="primary"] {
        background-color: #ff3333 !important; /* Vermell fort */
        color: white !important;
    }
    button[kind="primary"]:active {
        background-color: #cc0000 !important; /* Vermell fosc al clicar */
    }
    
    /* Amagar el menú de dalt a la dreta i el peu de pàgina per neteja */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. CONNEXIÓ AMB SUPABASE ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Error de connexió. Revisa els 'Secrets'.")
    st.stop()

# --- 4. CARREGAR TREBALLADORS ---
try:
    response = supabase.table("treballador").select("dni, nom").execute()
    if response.data:
        mapa_treballadors = {t['nom']: t['dni'] for t in response.data}
        llista_noms = list(mapa_treballadors.keys())
    else:
        mapa_treballadors = {}
        llista_noms = []
except Exception as e:
    mapa_treballadors = {}
    llista_noms = []

# --- 5. TÍTOL ---
st.markdown("<h1>Control Horari Outdoor</h1>", unsafe_allow_html=True)

if mapa_treballadors:
    
    # --- 6. RECORDAR USUARI (Automàtic) ---
    query_params = st.query_params
    nom_per_defecte = query_params.get("nom", None)
    
    index_inicial = 0
    if nom_per_defecte in llista_noms:
        index_inicial = llista_noms.index(nom_per_defecte)

    # Desplegable
    nom_seleccionat = st.selectbox(
        "Identifica't:", 
        llista_noms, 
        index=index_inicial
    )
    
    # Actualitzem la URL si canvia el nom (per la propera vegada)
    if nom_seleccionat != nom_per_defecte:
        st.query_params["nom"] = nom_seleccionat
    
    dni_actual = mapa_treballadors[nom_seleccionat]

    st.write("---")

    # --- 7. GPS I BOTONS ---
    # Obtenim la ubicació
    loc = get_geolocation()

    if loc:
        latitud = loc['coords']['latitude']
        longitud = loc['coords']['longitude']
        
        # Mostrem coordenades petites
        st.caption(f"📍 GPS Actiu: {latitud:.4f}, {longitud:.4f}")

        # --- BOTONS GEGANTS (UN SOTA L'ALTRE) ---
        
        # BOTÓ VERD (ENTRADA)
        # use_container_width=True -> Fa que ocupi tot l'ample del mòbil
        # type="secondary" -> El nostre CSS el pinta de VERD
        if st.button("ENTRADA", type="secondary", use_container_width=True):
            accio = "Entrada"
        else:
            accio = None
            
        st.write("") # Espai buit entre botons per estètica
        
        # BOTÓ VERMELL (SORTIDA)
        # type="primary" -> El nostre CSS el pinta de VERMELL
        if st.button("SORTIDA", type="primary", use_container_width=True):
            accio = "Sortida"

        # --- 8. GUARDAR DADES ---
        if accio:
            zona = pytz.timezone("Europe/Madrid")
            ara = datetime.now(zona)
            
            dades_a_guardar = {
                "dni_treballador": dni_actual,
                "tipus": accio,
                "data_hora": ara.isoformat(),
                "latitud": latitud,
                "longitud": longitud
            }

            try:
                supabase.table("fitxar").insert(dades_a_guardar).execute()
                st.balloons()
                st.success(f"✅ {accio} CORRECTA: {ara.strftime('%H:%M')}")
            except Exception as e:
                st.error(f"Error guardant: {e}")

    else:
        st.warning("📡 Buscant satèl·lits... (Espera uns segons)")

else:
    st.error("No hi ha treballadors a la base de dades.")
