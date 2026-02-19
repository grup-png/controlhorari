import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pytz
from streamlit_js_eval import get_geolocation

# --- 1. CONFIGURACIÓ VISUAL (MOBILE FIRST) ---
st.set_page_config(page_title="Fitxatge", page_icon="📍", layout="centered")

# --- 2. CONNEXIÓ SUPABASE ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Error de connexió. Revisa els 'Secrets' de Streamlit.")
    st.stop()

# --- 3. OBTENIR TREBALLADORS ---
try:
    response = supabase.table("treballador").select("dni, nom").execute()
    # Creem mapa Nom -> DNI
    treballador = {t['nom']: t['dni'] for t in response.data}
except:
    st.error("No s'han pogut carregar els treballador.")
    treballador = {}

# --- 4. TÍTOL I USUARI ---
st.title("📍 Control Horari")

if treballador:
    # Desplegable per triar qui ets
    nom_seleccionat = st.selectbox("Qui ets?", list(treballador.keys()))
    dni_real = treballador[nom_seleccionat]

    st.divider() # Línia separadora

    # --- 5. OBTENIR GPS (La part màgica) ---
    # Això demanarà permís al mòbil. Si no el dona, no deixa fitxar.
    loc = get_geolocation()

    if loc:
        # Si tenim GPS, guardem les dades
        latitud = loc['coords']['latitude']
        longitud = loc['coords']['longitude']
        
        st.success(f"📡 GPS Localitzat: {latitud:.4f}, {longitud:.4f}")
        
        st.write("### Què vols fer?")
        
        # --- 6. BOTONS GRANS (ENTRADA / SORTIDA) ---
        col1, col2 = st.columns(2)

        with col1:
            # Botó Verd d'Entrada
            if st.button("🟢 ENTRADA", use_container_width=True):
                accio = "Entrada"
                fer_registre = True
            else:
                fer_registre = False

        with col2:
            # Botó Vermell de Sortida
            if st.button("🔴 SORTIDA", use_container_width=True):
                accio = "Sortida"
                fer_registre = True
        
        # --- 7. GUARDAR A LA BASE DE DADES ---
        if fer_registre:
            # Agafem l'hora d'ara mateix
            zona = pytz.timezone("Europe/Madrid")
            ara = datetime.now(zona)
            
            # Preparem les dades
            dades = {
                "dni": dni_real,
                "tipus_moviment": accio,
                "latitud": latitud,
                "longitud": longitud,
                # Utilitzem data i hora separats com teníem abans
                "data": ara.strftime("%Y-%m-%d"),
                "hora": ara.strftime("%H:%M:%S")
            }
            
            try:
                supabase.table("registre_horari").insert(dades).execute()
                st.balloons() # Efecte visual xulo
                st.success(f"✅ {accio} registrada correctament a les {dades['hora']}")
            except Exception as e:
                st.error(f"Error al guardar: {e}")

    else:
        # Si encara no ha carregat el GPS o l'usuari ha dit que no
        st.warning("⏳ Esperant ubicació GPS... (Assegura't de donar permís al navegador)")

else:
    st.info("No hi ha treballadors a la base de dades.")
