import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import pytz
import pandas as pd

# ---------------------------------------------------------
# 1. CONFIGURACIÓ DE LA PÀGINA
# ---------------------------------------------------------
st.set_page_config(page_title="Control Horari", page_icon="🕒")
st.title("Control Horari 🏢")

# ---------------------------------------------------------
# 2. CONNEXIÓ SEGURA (SECRET MANAGEMENT)
# ---------------------------------------------------------
# Busquem les claus a la configuració interna de Streamlit Cloud
# Així no queden exposades al GitHub públicament.
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Error de configuració: No s'han trobat les claus secretes (Secrets).")
    st.stop()

# ---------------------------------------------------------
# 3. CARREGUEM ELS TREBALLADORS
# ---------------------------------------------------------
try:
    # Descarreguem DNI i NOM de la taula 'treballador'
    response = supabase.table("treballador").select("dni, nom").execute()
    llista_dades = response.data
    
    # Creem un diccionari: NOM -> DNI
    # Això ens permet mostrar el nom al desplegable però guardar el DNI internament
    if llista_dades:
        mapa_treballador = {item['nom']: item['dni'] for item in llista_dades}
        noms_per_losta = list(mapa_treballador.keys())
    else:
        mapa_treballador = {}
        noms_per_losta = []

except Exception as e:
    st.error(f"Error connectant amb la base de dades: {e}")
    st.stop()

# ---------------------------------------------------------
# 4. EL FORMULARI DE FITXATGE
# ---------------------------------------------------------
if noms_per_losta:
    with st.form("fitxatge_form", clear_on_submit=True):
        st.subheader("Nou Moviment")
        
        # A. Selecció del treballador
        nom_seleccionat = st.selectbox("Treballador/a:", noms_per_losta)
        
        # Recuperem el DNI ocultament
        dni_real = mapa_treballador[nom_seleccionat]
        
        # B. Tipus de moviment
        tipus = st.radio("Acció:", ["Entrada", "Sortida"], horizontal=True)
        
        # C. Ubicació (GPS)
        # Nota: Streamlit no agafa GPS automàtic per defecte per privacitat.
        # Aquí posem camps numèrics. Més endavant es poden automatitzar amb plugins.
        c1, c2 = st.columns(2)
        lat = c1.number_input("Latitud", value=41.38, format="%.5f")
        lon = c2.number_input("Longitud", value=2.17, format="%.5f")

        # Botó d'enviar
        enviat = st.form_submit_button("✅ Registrar Fitxatge", use_container_width=True)

        if enviat:
            # 1. Obtenim hora real (Zona Madrid/Barcelona)
            zona_bcn = pytz.timezone("Europe/Madrid")
            ara = datetime.now(zona_bcn)
            
            # 2. Preparem les dades
            dades = {
                "dni": dni_real,           # Clau forana
                "data": ara.strftime("%Y-%m-%d"),
                "hora": ara.strftime("%H:%M:%S"),
                "tipus_moviment": tipus,
                "latitud": lat,
                "longitud": lon
            }
            
            # 3. Guardem a Supabase
            try:
                supabase.table("registre_horari").insert(dades).execute()
                st.success(f"Perfecte! {tipus} registrat per a {nom_seleccionat} a les {dades['hora']}")
            except Exception as e:
                st.error(f"Error al guardar: {e}")

else:
    st.warning("⚠️ No hi ha treballadors a la base de dades. Afegeix-los a Supabase primer.")

# ---------------------------------------------------------
# 5. VISUALITZAR ÚLTIMS MOVIMENTS (Opcional)
# ---------------------------------------------------------
st.divider()
if st.checkbox("Veure últims registres"):
    try:
        # Consultem la vista o la taula. 
        # Si vas crear la 'vista_resum' (recomanat), canvia 'registre_horari' per 'vista_resum'
        res = supabase.table("registre_horari").select("*").order("id", desc=True).limit(5).execute()
        
        if res.data:
            df = pd.DataFrame(res.data)
            # Mostrem la taula neta
            st.dataframe(df)
        else:
            st.info("Encara no hi ha registres.")
    except Exception as e:
        st.error(f"Error carregant llista: {e}")
