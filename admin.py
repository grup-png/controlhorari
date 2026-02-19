import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pytz
from streamlit_js_eval import get_geolocation, get_user_agent

# --- 1. CONFIGURACIÓ DE LA PÀGINA ---
st.set_page_config(page_title="Outdoor", page_icon="🌲", layout="centered")

# --- 2. CSS PERSONALITZAT (ESTILS I COLORS) ---
st.markdown("""
    <style>
    h1 { text-align: center; margin-top: -20px; }

    /* Estil base botons */
    div.stButton > button {
        height: 90px;
        font-size: 30px !important;
        font-weight: 900 !important;
        border-radius: 15px;
        border: none;
        width: 100%;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.2);
    }

    /* ENTRADA (Verd) - secondary */
    button[kind="secondary"] {
        background-color: #2eb82e !important;
        color: white !important;
    }
    /* Si està deshabilitat (disabled), el posem gris fluix */
    button[kind="secondary"]:disabled {
        background-color: #e6ffe6 !important;
        color: #b3b3b3 !important;
        cursor: not-allowed;
    }

    /* SORTIDA (Vermell) - primary */
    button[kind="primary"] {
        background-color: #ff3333 !important;
        color: white !important;
    }
    /* Si està deshabilitat (disabled), el posem gris fluix */
    button[kind="primary"]:disabled {
        background-color: #ffe6e6 !important;
        color: #b3b3b3 !important;
        cursor: not-allowed;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. CONNEXIÓ SUPABASE ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Error de connexió.")
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
except:
    mapa_treballadors = {}
    llista_noms = []

# --- 5. TÍTOL ---
st.markdown("<h1>Control Horari Outdoor</h1>", unsafe_allow_html=True)

if mapa_treballadors:
    
    # --- 6. IDENTIFICACIÓ ---
    query_params = st.query_params
    nom_per_defecte = query_params.get("nom", None)
    
    index_inicial = 0
    if nom_per_defecte in llista_noms:
        index_inicial = llista_noms.index(nom_per_defecte)

    nom_seleccionat = st.selectbox("Identifica't:", llista_noms, index=index_inicial)
    
    if nom_seleccionat != nom_per_defecte:
        st.query_params["nom"] = nom_seleccionat
    
    dni_actual = mapa_treballadors[nom_seleccionat]

    st.write("---")

    # --- 7. CONSULTAR ESTAT ACTUAL (LÒGICA DE BLOQUEIG) ---
    # Busquem l'últim fitxatge d'aquesta persona
    estat_dins = False # Per defecte assumim que està fora
    try:
        ultim_mov = supabase.table("fitxar")\
            .select("tipus")\
            .eq("dni_treballador", dni_actual)\
            .order("data_hora", desc=True)\
            .limit(1)\
            .execute()
        
        if ultim_mov.data:
            darrer_tipus = ultim_mov.data[0]['tipus']
            if darrer_tipus == "Entrada":
                estat_dins = True
    except:
        pass # Si falla la consulta, assumim que està fora

    # --- 8. GPS I MÒBIL ---
    loc = get_geolocation()
    info_mobil = get_user_agent()

    if loc:
        latitud = loc['coords']['latitude']
        longitud = loc['coords']['longitude']
        
        # Informació Visual de l'Estat
        if estat_dins:
            st.info(f"🟢 Hola {nom_seleccionat}, actualment estàs **treballant**.")
        else:
            st.info(f"🔴 Hola {nom_seleccionat}, actualment estàs **fora**.")

        st.caption(f"📍 GPS Actiu | 📱 Dispositiu detectat")

        # --- 9. BOTONS GEGANTS (AMB BLOQUEIG) ---
        
        # ENTRADA (Verd) -> Només si ESTÀ FORA (estat_dins és False)
        # disabled = estat_dins (Si està dins, botó desactivat)
        btn_entrada = st.button("ENTRADA", type="secondary", use_container_width=True, disabled=estat_dins)
        
        st.write("") 
        
        # SORTIDA (Vermell) -> Només si ESTÀ DINS (estat_dins és True)
        # disabled = not estat_dins (Si NO està dins, botó desactivat)
        btn_sortida = st.button("SORTIDA", type="primary", use_container_width=True, disabled=not estat_dins)

        # Lògica d'acció
        accio = None
        if btn_entrada:
            accio = "Entrada"
        elif btn_sortida:
            accio = "Sortida"

        # --- 10. GUARDAR DADES ---
        if accio:
            zona = pytz.timezone("Europe/Madrid")
            ara = datetime.now(zona)
            
            model_mobil = info_mobil if info_mobil else "Desconegut"
            
            dades_a_guardar = {
                "dni_trebal
