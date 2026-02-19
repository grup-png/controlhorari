import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pytz
from streamlit_js_eval import get_geolocation

# --- 1. CONFIGURACIÓ DE LA PÀGINA ---
st.set_page_config(page_title="Fitxatge", page_icon="📍", layout="centered")

# --- 2. CONNEXIÓ AMB SUPABASE ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Error de connexió. Revisa els 'Secrets' de Streamlit.")
    st.stop()

# --- 3. CARREGAR TREBALLADORS (Taula: treballador) ---
try:
    # Atenció: Busquem a la taula 'treballador' (singular)
    response = supabase.table("treballador").select("dni, nom").execute()
    
    # Creem un diccionari per saber quin DNI té cada NOM
    if response.data:
        mapa_treballadors = {t['nom']: t['dni'] for t in response.data}
    else:
        mapa_treballadors = {}
        
except Exception as e:
    st.error(f"Error carregant la taula 'treballador': {e}")
    mapa_treballadors = {}

# --- 4. DISSENY DE L'APP ---
st.title("📍 Control Horari")

if mapa_treballadors:
    # A. SELECCIÓ DE L'USUARI
    nom_seleccionat = st.selectbox("Selecciona el teu nom:", list(mapa_treballadors.keys()))
    
    # Recuperem el DNI internament
    dni_actual = mapa_treballadors[nom_seleccionat]

    st.write("---")

    # B. OBTENCIÓ DEL GPS
    # Això demanarà permís al mòbil per saber on ets
    loc = get_geolocation()

    if loc:
        # Si tenim GPS, guardem les coordenades
        latitud = loc['coords']['latitude']
        longitud = loc['coords']['longitude']
        
        st.success(f"📡 Ubicació detectada")

        # C. BOTONS D'ACCIÓ (ENTRADA / SORTIDA)
        col1, col2 = st.columns(2)
        accio = None

        with col1:
            if st.button("🟢 ENTRADA", use_container_width=True):
                accio = "Entrada"
        
        with col2:
            if st.button("🔴 SORTIDA", use_container_width=True):
                accio = "Sortida"

        # D. GUARDAR A LA BASE DE DADES (Taula: fitxar)
        if accio:
            # 1. Agafem la data i hora actual de la zona correcta
            zona = pytz.timezone("Europe/Madrid")
            ara = datetime.now(zona)
            
            # 2. Preparem les dades EXACTES per a la taula 'fitxar'
            dades_a_guardar = {
                "dni_treballador": dni_actual,  # Camp 'dni_treballador'
                "tipus": accio,                 # Camp 'tipus'
                "data_hora": ara.isoformat(),   # Camp 'data_hora' (Tot junt)
                "latitud": latitud,             # Camp 'latitud'
                "longitud": longitud            # Camp 'longitud'
            }

            try:
                # Inserim a la taula 'fitxar'
                supabase.table("fitxar").insert(dades_a_guardar).execute()
                
                # Missatge d'èxit
                st.balloons()
                st.success(f"✅ {accio} registrada correctament per a {nom_seleccionat}!")
                st.info(f"Hora: {ara.strftime('%d/%m/%Y %H:%M:%S')}")
            
            except Exception as e:
                st.error(f"Error al guardar a la taula 'fitxar': {e}")

    else:
        st.warning("⏳ Esperant senyal GPS... (Activa la ubicació o refresca la pàgina)")

else:
    st.info("No s'han trobat dades a la taula 'treballador'.")
