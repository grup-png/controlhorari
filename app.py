import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pytz
from streamlit_js_eval import get_geolocation

# --- 1. CONFIGURACIÓ DE LA PÀGINA ---
st.set_page_config(page_title="Outdoor", page_icon="🌲", layout="centered")

# --- 2. CSS PERSONALITZAT (ESTILS I COLORS) ---
# Això és el que fa la màgia dels colors i la mida dels botons
st.markdown("""
    <style>
    /* 1. Centrar el títol */
    h1 {
        text-align: center;
        margin-bottom: 30px;
    }
    
    /* 2. Estil general dels botons (Grans i negreta) */
    div.stButton > button {
        width: 100%;            /* Ocupar tot l'ample */
        height: 80px;           /* Més alts */
        font-size: 24px !important; /* Lletra gran */
        font-weight: 800 !important; /* Lletra gruixuda */
        border-radius: 12px;    /* Bordes arrodonits */
        border: none;
        margin-bottom: 10px;
    }

    /* 3. Botó d'ENTRADA (Verd) - És el primer botó que apareix */
    div.stButton:nth-of-type(1) > button {
        background-color: #28a745 !important; /* Verd intens */
        color: white !important;
    }
    
    /* 4. Efecte quan passes per sobre (Entrada) */
    div.stButton:nth-of-type(1) > button:hover {
        background-color: #218838 !important;
    }

    /* 5. Botó de SORTIDA (Vermell) - És el segon botó que apareix */
    div.stButton:nth-of-type(2) > button {
        background-color: #dc3545 !important; /* Vermell intens */
        color: white !important;
    }

    /* 6. Efecte quan passes per sobre (Sortida) */
    div.stButton:nth-of-type(2) > button:hover {
        background-color: #c82333 !important;
    }
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
    st.error(f"Error carregant dades: {e}")
    mapa_treballadors = {}
    llista_noms = []

# --- 5. TÍTOL CENTRAT ---
# Utilitzem markdown per centrar-ho ja que st.title no deixa per defecte
st.markdown("<h1>Control Horari Outdoor</h1>", unsafe_allow_html=True)

if mapa_treballadors:
    
    # --- 6. RECORDAR USUARI (Lògica de Query Params) ---
    # Mirem si a l'enllaç web hi ha un nom guardat (?nom=Pep)
    query_params = st.query_params
    nom_per_defecte = query_params.get("nom", None)
    
    index_inicial = 0
    if nom_per_defecte in llista_noms:
        index_inicial = llista_noms.index(nom_per_defecte)

    # El Desplegable
    nom_seleccionat = st.selectbox(
        "Qui ets?", 
        llista_noms, 
        index=index_inicial
    )
    
    # Guardem la selecció a la URL per la propera vegada
    if nom_seleccionat != nom_per_defecte:
        st.query_params["nom"] = nom_seleccionat
    
    # Recuperem el DNI
    dni_actual = mapa_treballadors[nom_seleccionat]

    st.write("---")

    # --- 7. GPS I BOTONS ---
    loc = get_geolocation()

    if loc:
        latitud = loc['coords']['latitude']
        longitud = loc['coords']['longitude']
        
        # Missatge GPS discret
        st.caption(f"📡 GPS: {latitud:.4f}, {longitud:.4f}")

        # BOTÓ 1: ENTRADA (Es pintarà VERD pel CSS de dalt)
        if st.button("ENTRADA"):
            accio = "Entrada"
        else:
            accio = None
            
        # BOTÓ 2: SORTIDA (Es pintarà VERMELL pel CSS de dalt)
        if st.button("SORTIDA"):
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
                st.success(f"✅ {accio} OK: {ara.strftime('%H:%M')}")
            except Exception as e:
                st.error(f"Error: {e}")

    else:
        st.warning("⏳ Buscant satèl·lits GPS...")

else:
    st.info("No hi ha treballadors a la base de dades.")
