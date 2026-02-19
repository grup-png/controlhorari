import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, timedelta
import io

# --- 1. CONFIGURACIÓ ---
st.set_page_config(page_title="Admin Outdoor", page_icon="📊", layout="centered")

# CSS per centrar títol i estil del botó
st.markdown("""
    <style>
    h1 { text-align: center; }
    /* Estil per fer el botó més gran i net */
    div.stDownloadButton > button {
        width: 100%;
        background-color: white !important;
        color: black !important;
        border: 2px solid #ccc !important;
        font-weight: bold !important;
        height: 60px;
    }
    div.stDownloadButton > button:hover {
        background-color: #f0f0f0 !important;
        border-color: #999 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. CONNEXIÓ SUPABASE ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Error connectant a Supabase.")
    st.stop()

# --- 3. FUNCIONS AUXILIARS ---
def obtenir_treballadors():
    try:
        response = supabase.table("treballador").select("dni, nom").execute()
        return {t['nom']: t['dni'] for t in response.data}
    except:
        return {}

def calcular_hores(df_mes):
    """
    Aquesta funció és el cervell. Organitza les dades per a l'Excel.
    """
    resultats = []
    
    # Agrupem per dia
    dies = df_mes['data_hora'].dt.date.unique()
    dies = sorted(dies)
    
    total_hores_mes = timedelta(0)

    for dia in dies:
        # Agafem fitxatges d'aquell dia
        registres_dia = df_mes[df_mes['data_hora'].dt.date == dia].sort_values('data_hora')
        
        # Preparem la fila per l'Excel
        fila = {'DATA': dia.strftime('%d/%m/%Y')}
        
        entrades = registres_dia[registres_dia['tipus'] == 'Entrada']['data_hora'].tolist()
        sortides = registres_dia[registres_dia['tipus'] == 'Sortida']['data_hora'].tolist()
        
        # Emparellament (Entrada 1 -> Sortida 1, Entrada 2 -> Sortida 2...)
        # Si algú s'oblida de fitxar sortida, el sistema agafa fins on pot.
        max_parelles = max(len(entrades), len(sortides))
        
        temps_treballat_dia = timedelta(0)
        
        for i in range(max_parelles):
            # Hora Entrada
            hora_in = entrades[i].strftime('%H:%M') if i < len(entrades) else ""
            fila[f'ENTRADA {i+1}'] = hora_in
            
            # Hora Sortida
            hora_out = sortides[i].strftime('%H:%M') if i < len(sortides) else ""
            fila[f'SORTIDA {i+1}'] = hora_out
            
            # Càlcul de temps
            if i < len(entrades) and i < len(sortides):
                t_in = entrades[i]
                t_out = sortides[i]
                diff = t_out - t_in
                temps_treballat_dia += diff
        
        # Format del total dia (Hores:Minuts)
        total_seconds = int(temps_treballat_dia.total_seconds())
        hores, residu = divmod(total_seconds, 3600)
        minuts, _ = divmod(residu, 60)
        fila['TOTAL DIA'] = f"{hores:02}:{minuts:02}"
        
        resultats.append(fila)
        total_hores_mes += temps_treballat_dia

    return resultats, total_hores_mes

# --- 4. INTERFÍCIE (UI) ---
st.markdown("<h1>Control Horari Outdoor</h1>", unsafe_allow_html=True)

treballadors = obtenir_treballadors()

if treballadors:
    # A. Selecció de Treballador
    col1, col2 = st.columns(2)
    with col1:
        nom_seleccionat = st.selectbox("Selecciona Treballador", list(treballadors.keys()))
        dni_seleccionat = treballadors[nom_seleccionat]
    
    # B. Selecció de Calendari (Mes i Any)
    with col2:
        mesos = {
            1: "Gener", 2: "Febrer", 3: "Març", 4: "Abril", 5: "Maig", 6: "Juny",
            7: "Juliol", 8: "Agost", 9: "Setembre", 10: "Octubre", 11: "Novembre", 12: "Desembre"
        }
        col_mes, col_any = st.columns(2)
        mes_actual = datetime.now().month
        any_actual = datetime.now().year
        
        mes_triat_nom = col_mes.selectbox("Mes", list(mesos.values()), index=mes_actual-1)
        any_triat = col_any.number_input("Any", value=any_actual, step=1)
        
        # Convertim el nom del mes a número (ex: "Febrer" -> 2)
        mes_triat_num = list(mesos.keys())[list(mesos.values()).index(mes_triat_nom)]

    st.write("---")

    # --- 5. GENERACIÓ DE L'INFORME ---
    # Botó per pre-calcular (opcional, però va bé per debug)
    # Aquí fem directament la lògica dins del download button per eficiència
    
    # Recuperem dades de Supabase
    query = supabase.table("fitxar").select("*").eq("dni_treballador", dni_seleccionat).execute()
    
    buffer = io.BytesIO() # Memòria per guardar l'Excel
    dades_disponibles = False
    nom_fitxer = f"Informe_{nom_seleccionat}_{mes_triat_nom}_{any_triat}.xlsx"
    
    if query.data:
        df = pd.DataFrame(query.data)
        
        # Convertim columna text a datetime
        df['data_hora'] = pd.to_datetime(df['data_hora'])
        
        # Filtrem pel mes i any seleccionats
        df_mes = df[
            (df['data_hora'].dt.month == mes_triat_num) & 
            (df['data_hora'].dt.year == any_triat)
        ]
        
        if not df_mes.empty:
            dades_disponibles = True
            
            # CALCULEM TOTES LES DADES
            files_excel, total_mes_delta = calcular_hores(df_mes)
            df_export = pd.DataFrame(files_excel)
            
            # Format total mes
            sec_total = int(total_mes_delta.total_seconds())
            hh, rem = divmod(sec_total, 3600)
            mm, _ = divmod(rem, 60)
            text_total_mes = f"{hh} hores i {mm} minuts"

            # CREACIÓ DE L'EXCEL (Amb format maco)
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                # 1. Escriure les dades principals
                df_export.to_excel(writer, sheet_name='Informe', startrow=4, index=False)
                
                workbook = writer.book
                worksheet = writer.sheets['Informe']
                
                # 2. Formats
                bold = workbook.add_format({'bold': True})
                titol_format = workbook.add_format({'bold': True, 'font_size': 14})
                
                # 3. Encapçalament (Nom, DNI, Data)
                worksheet.write('A1', f"NOM: {nom_seleccionat}", titol_format)
                worksheet.write('A2', f"DNI: {dni_seleccionat}", bold)
                worksheet.write('A3', f"PERÍODE: {mes_triat_nom} {any_triat}", bold)
                
                # 4. Total final a baix de tot
                fila_final = 4 + len(df_export) + 2
                worksheet.write(fila_final, 0, "TOTAL HORES MES:", bold)
                worksheet.write(fila_final, 1, text_total_mes, bold)
                
                # Ajustar amplada columnes
                worksheet.set_column(0, 0, 15) # Data
                worksheet.set_column(1, 10, 12) # Entrades/Sortides

    # --- 6. BOTÓ BLANC "INFORME" ---
    if dades_disponibles:
        st.download_button(
            label="📄 INFORME",
            data=buffer,
            file_name=nom_fitxer,
            mime="application/vnd.ms-excel"
        )
    else:
        st.warning("No hi ha fitxatges per a aquest treballador en aquest mes.")
        st.download_button("📄 INFORME (Buit)", data=b"", disabled=True)

else:
    st.info("No s'han trobat treballadors.")
