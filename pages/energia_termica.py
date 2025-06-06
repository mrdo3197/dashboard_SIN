import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import os
import login as login

st.set_page_config(page_title="Dashboard Sistema Interconectado Nacional.", layout="wide")
login.generarLogin()

if 'usuario' in st.session_state:
    # st.set_page_config(page_title="Análisis de Energía Térmica.", layout="wide")
    # st.header('Análisis de Energía Térmica.')
    st.title("🔍 Análisis de Generación y Emisiones Térmicas en Colombia (2000-2025)")

    # Leer archivos automáticamente desde la carpeta actual
    try:
        df_gen = pd.read_csv("generacion.csv")
        df_ppp = pd.read_csv("ppp.csv")
        df_gt = pd.read_excel("datagt.xlsx")
    except FileNotFoundError:
        st.error("❌ No se encontraron los archivos necesarios en la carpeta actual.")
        st.stop()

    # Procesamiento de fechas
    df_gen['Fecha'] = pd.to_datetime(df_gen['Fecha']).dt.date
    df_ppp['Fecha'] = pd.to_datetime(df_ppp['Fecha']).dt.date

    start_date = datetime.date(2000, 1, 1)
    end_date = datetime.date(2025, 3, 1)

    df_gen_filtrado = df_gen[(df_gen['Fecha'] >= start_date) & (df_gen['Fecha'] <= end_date)].copy()
    df_ppp_filtrado = df_ppp[(df_ppp['Fecha'] >= start_date) & (df_ppp['Fecha'] <= end_date)].copy()

    # Totales por tipo de combustible
    totales = df_gt[['Carbón', 'Gas', 'Gas Importado', 'Líquidos']].sum()
    factores_emision = {
        'Carbón': 820,
        'Gas': 490,
        'Gas Importado': 490,
        'Líquidos': 770
    }

    # Agrupación general
    df_agrupado = df_gen[df_gen['TipoGeneracion'] == 'Combustible fósil'].groupby('Fecha').agg({
        'gen_procentaje': 'sum',
        'GeneracionRealEstimada': 'sum'
    }).reset_index()

    # Agrupar tipos de generación
    def agrupar(tipo):
        return df_gen_filtrado[df_gen_filtrado['TipoGeneracion'] == tipo].groupby('Fecha')['GeneracionRealEstimada'].sum().reset_index()

    df_fosil = agrupar('Combustible fósil')
    df_hidro = agrupar('Hidráulica')
    df_solar = agrupar('Solar')
    df_eolica = agrupar('Eólica')

    # Emisiones
    totales_generacion = totales
    totales_emisiones = totales_generacion * 1000 * pd.Series(factores_emision)
    totales_emisiones_kton = totales_emisiones / 1e6

    # Unir PPP
    df_final = pd.merge(
        df_agrupado,
        df_ppp_filtrado[['Fecha', 'PPP Bolsa diario']],
        on='Fecha',
        how='inner'
    ).rename(columns={'PPP Bolsa diario': 'PPP'})

    correlacion = df_final['gen_procentaje'].corr(df_final['PPP'])

    st.subheader("📈 1. Correlación entre participación térmica y PPP")
    st.write(f"**Correlación**: `{correlacion:.2f}`")

    fig_corr = px.scatter(
        df_final, x='gen_procentaje', y='PPP',
        trendline="ols",
        labels={'gen_procentaje': '% de Generación Térmica', 'PPP': 'PPP ($/kWh)'},
        title="Relación entre % de Generación Térmica y PPP"
    )
    st.plotly_chart(fig_corr, use_container_width=True)

    st.subheader("⚡ 2. Generación de energía por tipo")
    df_merged = (
        df_fosil.rename(columns={'GeneracionRealEstimada': 'Fósil'})
        .merge(df_hidro.rename(columns={'GeneracionRealEstimada': 'Hidro'}), on='Fecha', how='outer')
        .merge(df_solar.rename(columns={'GeneracionRealEstimada': 'Solar'}), on='Fecha', how='outer')
        .merge(df_eolica.rename(columns={'GeneracionRealEstimada': 'Eólica'}), on='Fecha', how='outer')
    ).sort_values('Fecha')

    fig_line = px.line(df_merged, x='Fecha', y=['Fósil', 'Hidro', 'Solar', 'Eólica'],
                    title="Generación Estimada por Fuente (GWh)",
                    labels={'value': 'Generación (GWh)', 'variable': 'Tipo de Energía'})
    st.plotly_chart(fig_line, use_container_width=True)

    # ---- 3. EMISIONES POR TIPO DE ENERGÍA A TRAVÉS DEL TIEMPO ----

    st.subheader("⚡ 3. Emisiones de CO₂eq por Tipo de Energía")

    # Factores de emisión (kg CO₂eq/MWh)
    factores_emision = {
        'Combustible fósil': 820,  # Valor promedio ponderado de tus cálculos térmicos
        'Hidráulica': 100,
        'Solar': 50,
        'Eólica': 15
    }

    # Procesamiento: Multiplicar generación por factor de emisión
    def calcular_emisiones(tipo):
        df = df_gen_filtrado[df_gen_filtrado['TipoGeneracion'] == tipo].copy()
        df['Emisiones'] = df['GeneracionRealEstimada'] * factores_emision[tipo] / 1e6  # Convertir a kton CO₂eq
        return df.groupby('Fecha')['Emisiones'].sum().reset_index()

    # DataFrames por tipo
    df_emis_fosil = calcular_emisiones('Combustible fósil').rename(columns={'Emisiones': 'Fósil'})
    df_emis_hidro = calcular_emisiones('Hidráulica').rename(columns={'Emisiones': 'Hidro'})
    df_emis_solar = calcular_emisiones('Solar').rename(columns={'Emisiones': 'Solar'})
    df_emis_eolica = calcular_emisiones('Eólica').rename(columns={'Emisiones': 'Eólica'})

    # Unir todos los DataFrames
    df_emisiones_total = (
        df_emis_fosil.merge(df_emis_hidro, on='Fecha', how='outer')
        .merge(df_emis_solar, on='Fecha', how='outer')
        .merge(df_emis_eolica, on='Fecha', how='outer')
    ).fillna(0).sort_values('Fecha')

    # Gráfico de áreas apiladas
    fig_emisiones_temporales = px.area(
        df_emisiones_total,
        x='Fecha',
        y=['Fósil', 'Hidro', 'Solar', 'Eólica'],
        title="Emisiones de CO₂eq por Fuente (kton)",
        labels={'value': 'Emisiones (kton CO₂eq)', 'variable': 'Tipo de Energía'},
        color_discrete_map={
            'Fósil': '#DC143C',  # Rojo
            'Hidro': '#1E90FF',   # Azul
            'Solar': '#FFD700',   # Amarillo
            'Eólica': '#32CD32'   # Verde
        }
    )

    # Personalización
    fig_emisiones_temporales.update_layout(
        hovermode='x unified',
        yaxis_title='Emisiones Acumuladas (kton CO₂eq)',
        xaxis_title='Fecha'
    )

    st.plotly_chart(fig_emisiones_temporales, use_container_width=True)

    # ---- METRICAS COMPARATIVAS ----
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Emisiones Térmicas", 
                f"{df_emisiones_total['Fósil'].sum():,.0f} kton", 
                delta_color="inverse")
    with col2:
        st.metric("Emisiones Hidro", 
                f"{df_emisiones_total['Hidro'].sum():,.0f} kton")
    with col3:
        st.metric("Emisiones Solar+Eólica", 
                f"{(df_emisiones_total['Solar'].sum() + df_emisiones_total['Eólica'].sum()):,.0f} kton",
                help="Suma de solar y eólica")
        

    st.subheader("🔥 4. Total de generación térmica por tipo de combustible")
    df_totales = totales.reset_index()
    df_totales.columns = ['Combustible', 'GWh']

    fig_bar = px.bar(df_totales, x='Combustible', y='GWh',
                    color='Combustible',
                    text='GWh',
                    title="Total Generación Térmica por Tipo (GWh)")
    fig_bar.update_traces(texttemplate='%{text:.2s}', textposition='outside')
    st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("🌍 5. Emisiones de CO₂ eq por tipo de combustible")
    df_emisiones = totales_emisiones_kton.reset_index()
    df_emisiones.columns = ['Combustible', 'kton CO₂eq']
    df_emisiones['FE (kg/MWh)'] = df_emisiones['Combustible'].map(factores_emision)

    fig_emisiones = px.bar(
        df_emisiones, x='Combustible', y='kton CO₂eq',
        text='kton CO₂eq', color='Combustible',
        title="Emisiones Totales de CO₂ eq en Plantas Térmicas (kton)",
        hover_data=['FE (kg/MWh)']
    )
    fig_emisiones.update_traces(texttemplate='%{text:.0f}', textposition='outside')
    st.plotly_chart(fig_emisiones, use_container_width=True)

    st.success("✅ Las emisiones evitables con ERNC son **201.997 kton CO₂eq** generadas por las plantas térmicas.")

    st.subheader("📊 Tabla Comparativa: Costos vs Emisiones por Tipo de Energía")

    # 1. Definir parámetros clave (en USD/MWh y kg CO₂eq/MWh)
    parametros = {
        'Combustible fósil': {'costo': 75, 'fe': 820},
        'Hidráulica': {'costo': 35, 'fe': 100},
        'Solar': {'costo': 60, 'fe': 50},
        'Eólica': {'costo': 55, 'fe': 15}
    }

    # 2. Calcular métricas agregadas por tipo
    def calcular_metricas(tipo):
        df = df_gen_filtrado[df_gen_filtrado['TipoGeneracion'] == tipo]
        generacion_gwh = df['GeneracionRealEstimada'].sum() / 1000  # Convertir a GWh si está en MWh
        return {
            'Generación (GWh)': generacion_gwh,
            'Costo Unitario (USD/MWh)': parametros[tipo]['costo'],
            'Factor Emisión (kg CO₂eq/MWh)': parametros[tipo]['fe'],
            'Costo Total (M USD)': (generacion_gwh * parametros[tipo]['costo']) / 1000,
            'Emisiones Totales (kton CO₂eq)': (generacion_gwh * parametros[tipo]['fe']) / 1000,
            'Emisiones/Millón USD': (parametros[tipo]['fe'] / parametros[tipo]['costo']) * 1000
        }

    # 3. Construir tabla comparativa
    tabla_comparativa = pd.DataFrame.from_dict(
        {tipo: calcular_metricas(tipo) for tipo in parametros},
        orient='index'
    )

    # 4. Formatear visualización en Streamlit
    st.dataframe(
        tabla_comparativa.style.format({
            'Generación (GWh)': '{:,.0f}',
            'Costo Unitario (USD/MWh)': '{:,.0f}',
            'Factor Emisión (kg CO₂eq/MWh)': '{:,.0f}',
            'Costo Total (M USD)': '{:,.2f}',
            'Emisiones Totales (kton CO₂eq)': '{:,.1f}',
            'Emisiones/Millón USD': '{:,.0f}'
        }).background_gradient(cmap='Blues', subset=['Emisiones Totales (kton CO₂eq)'])
        .background_gradient(cmap='Greens', subset=['Costo Total (M USD)'])
        .highlight_max(subset=['Emisiones/Millón USD'], color='#FF7F7F')
        .set_properties(**{'text-align': 'center'}),
        height=400,
        use_container_width=True
    )

    # 5. Gráfico de dispersión costos vs emisiones
    st.subheader("📈 Relación Costo-Emisión por Tecnología")
    fig_scatter = px.scatter(
        tabla_comparativa.reset_index(),
        x='Costo Unitario (USD/MWh)',
        y='Factor Emisión (kg CO₂eq/MWh)',
        size='Generación (GWh)',
        color='index',
        hover_name='index',
        labels={'index': 'Tipo de Energía'},
        title="Eficiencia Ambiental vs Costo (Tamaño = Generación)",
        size_max=40,
        color_discrete_sequence=['#DC143C', '#1E90FF', '#FFD700', '#32CD32']
    )
    fig_scatter.update_layout(showlegend=False)
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("### 🔎 Insights Clave")
    st.write(f"""
    1. **Tecnología más contaminante por dólar**: {tabla_comparativa['Emisiones/Millón USD'].idxmax()} 
    ({(tabla_comparativa['Emisiones/Millón USD'].max()):,.0f} kg CO₂eq por millón USD invertido)
    
    2. **Tecnología más eficiente**: {tabla_comparativa['Emisiones/Millón USD'].idxmin()} 
    ({(tabla_comparativa['Emisiones/Millón USD'].min()):,.0f} kg CO₂eq por millón USD)

    3. **Reemplazo óptimo**: Cada GWh de energía fósil reemplazado por eólica evitaría 
    {(parametros['Combustible fósil']['fe'] - parametros['Eólica']['fe']):,.0f} toneladas de CO₂eq.
    """)