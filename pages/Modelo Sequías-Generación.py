# 1. Librerías
import streamlit as st
import altair as alt
import pandas as pd
import geopandas as gpd
import login as login
from sklearn import linear_model
from sklearn import metrics
from scipy.stats import pearsonr

st.set_page_config(page_title="Dashboard Sistema Interconectado Nacional.", layout="wide")
alt.data_transformers.enable("vegafusion")

login.generarLogin()

if 'usuario' in st.session_state:
    st.header(':orange[Dashboard] Modelo predictivo.')

    # 2. Cargar generacion
    datos_reg = pd.read_csv("datos_regresion.csv",
                        encoding = "utf-8")

    # 3. generacion para listas de selección

    plantas = list(datos_reg["NombrePlanta"].sort_values().unique())

    # 4. Configuración de la página


    # 5.2. Gráficas
    main = st.container(border=False)

    with main:
        columns1 = st.columns(1,
                            border=False)

        with columns1[0]:

            columns2 = st.columns([0.3, 0.8, 0.2])
            with columns2[1]:

                planta = st.selectbox("Planta",
                                    plantas)
            
            # Modelo

            filtro = datos_reg["NombrePlanta"] == planta
            source = datos_reg.loc[filtro]

            regresion = linear_model.LinearRegression()

            X = source["SPI3"].values.reshape(-1, 1)
            y = source["g_men_p"]

            

            modelo = regresion.fit(X, y)
            b = modelo.intercept_
            m = modelo.coef_

            eq = f'y = {m[0]:.2f}x + {b:.2f}'
            

            r = pearsonr(source["SPI3"], y)[0]
            p_value = pearsonr(source["SPI3"], y)[1]

            stat = f'r = {r:.2f}, p-value < 0.05'

            # Base chart with points
            points = alt.Chart(source).mark_circle(size=60, color="lightblue").encode(
                x=alt.X('SPI3', title="SPI3"),
                y=alt.Y('g_men_p', title="Generación Mensual Promedio [GWh]")
            ).properties(width=450, height=480)

            # Regression line
            regression = points.transform_regression(
                'SPI3', 'g_men_p'
            ).mark_line(color="#3498db")

            # Equation text
            equation = alt.Chart(pd.DataFrame({'x': [2], 'y': [5], 'text': [eq]})).mark_text(
                align='left',
                baseline='top',
                fontSize=16,
                # font='Arial',
                # strokeWidth=0.5,
                # fontWeight='bold',
                # color='black',
                xOffset=80,  # Pixels from left edge
                yOffset=150   # Pixels from top edge
            ).encode(
                text="text")

            correlation = alt.Chart(pd.DataFrame({'x': [2], 'y': [5], 'text': [stat]})).mark_text(
                align='left',
                baseline='top',
                fontSize=16,
                # fontWeight='bold',
                # color='black',
                xOffset=80,  # Pixels from left edge
                yOffset= 170   # Pixels from top edge
            ).encode(
                text="text")

            # Combine all layers
            chart = (points + regression + equation + correlation)
            
            st.altair_chart(chart,
                            use_container_width = True)
            

            columns2 = st.columns([1,0.2,1],
                                border=False)
            
            with columns2[0]:

                SPI_entrada = st.number_input("Valor de SPI a evaluar")
            with columns2[2]:
                gen_pred = modelo.predict([[SPI_entrada]])
                st.metric("Generación predicha [GWh]", gen_pred.round(2))
