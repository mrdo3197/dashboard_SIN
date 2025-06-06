# 1. Librerías
import streamlit as st
import altair as alt
import pandas as pd
import login as login
# import geopandas as gpd


st.set_page_config(page_title="Dashboard Sistema Interconectado Nacional.", layout="wide")
login.generarLogin()

if 'usuario' in st.session_state:
  
  st.header(':orange[Dashboard] Sistema Interconectado Nacional.')


  alt.data_transformers.enable("vegafusion")

# 2. Cargar generacion
  generacion = pd.read_csv("generacion.csv",
                      encoding = "utf-8")
  generacion["Fecha"] = pd.to_datetime(generacion["Fecha"])
  generacion["GeneracionRealEstimada"] = generacion["GeneracionRealEstimada"] * 10 ** -6

  fpo = pd.read_csv("FPO.csv",
                      encoding = "utf-8")
  fpo["Fecha Operación"] = pd.to_datetime(fpo["Fecha Operación"])

# 3. generacion para listas de selección
  fuentes = ["Todas"] + list(generacion["TipoGeneracion"].sort_values().unique())
  plantas = ["Todas"] + list(generacion["NombrePlanta"].sort_values().unique())
  escalas = ["Diaria", "Mensual", "Anual"]
  codigo_escala = ["D", "ME", "YE"]

# 4. Configuración de la página



# 5. Interfaz
# 5.1. Barra lateral
# Título
  st.sidebar.subheader("Evolución del Sistema Interconectado Nacional (SIN)")

# Filtros de búsqueda
  min_value = generacion["Fecha"].min()
  max_value = generacion["Fecha"].max()
  format = "DD/MM/YYYY"

  fecha_inicial = st.sidebar.date_input(label = "Fecha inicial",
                                        value = min_value,
                                        min_value = min_value,
                                        max_value = max_value,
                                        help = "Consultas disponibles desde 1995/7/20",
                                        format = format)

  fecha_final = st.sidebar.date_input(label = "Fecha final",
                                      value = max_value,
                                      min_value = min_value,
                                      max_value = max_value,
                                      help = "Consultas disponibles hasta 2025/5/30",
                                      format = format)

# Menús desplegables
  fuente = st.sidebar.selectbox("Fuente",
                                fuentes)

# Mostrar solo plantas de determinada fuente cuando haya una fuente seleccionada
  if fuente != "Todas":
    filtro = generacion["TipoGeneracion"] == fuente
    plantas = ["Todas"] + list(generacion.loc[filtro, "NombrePlanta"].sort_values().unique())

  planta = st.sidebar.selectbox("Planta",
                                plantas)
  escala = st.sidebar.selectbox("Escala",
                                escalas)

# Valores de fechas predeterminados
  if fecha_inicial == None:
    fecha_inicial = min_value
  if fecha_final == None:
    fecha_final = max_value


# Escala de agregación de los datos
  if escala == "Diaria":
    s = codigo_escala[0]
  elif escala == "Mensual":
    s = codigo_escala[1]
  else:
    s = codigo_escala[2]

# Agregación de los datos de generación de acuerdo con la escala seleccionada
  if escala == "Diaria":
    generacion = generacion
  else:
      generacion = (
        generacion.groupby(
          [pd.Grouper(key = 'Fecha',
                      freq = s),
                      'NombrePlanta',
                      'TipoGeneracion']
                          ).agg({'GeneracionRealEstimada': 'sum'}
                                ).reset_index()
                    )

# Filtro de los datos
  filtro_fecha = (generacion["Fecha"] >= pd.to_datetime(fecha_inicial)) & (generacion["Fecha"] <= pd.to_datetime(fecha_final))

# Filtro para Fuente y Planta con valor "Todas"
  if fuente == "Todas" and planta == "Todas":
    filtro = filtro_fecha
    generacion_filtrada = generacion.loc[filtro].groupby(["Fecha", "TipoGeneracion"]).sum("GeneracionRealEstimada").reset_index()
# Filtro para Fuente específica y Planta con valor "Todas"
  elif fuente != "Todas" and planta == "Todas":
    filtro = filtro_fecha & (generacion["TipoGeneracion"] == fuente)
    generacion_filtrada = generacion.loc[filtro].groupby(["Fecha", "TipoGeneracion"]).sum("GeneracionRealEstimada").reset_index()
# Filtro para todas o una fuente específica y Planta con valor específico
  elif planta != "Todas":
    filtro = filtro_fecha & (generacion["NombrePlanta"] == planta)
    generacion_filtrada = generacion.loc[filtro]

# 5.2. Gráficas
  main = st.container(border=False)

# Filtro para generación fuente hidráulica y combustibles fósiles
  filt_mayor = (generacion_filtrada["TipoGeneracion"] == "Combustible fósil") | (generacion_filtrada["TipoGeneracion"] == "Hidráulica")
  gen_mayor = generacion_filtrada.loc[filt_mayor]
# Filtro para generación fuente solar, biomasa y eólica
  filt_menor = (generacion_filtrada["TipoGeneracion"] != "Combustible fósil") & (generacion_filtrada["TipoGeneracion"] != "Hidráulica")
  gen_menor = generacion_filtrada.loc[filt_menor]

  with main:
    columns = st.columns(3,
                        border=False)

    with columns[0]:
      
    # st.markdown("Generación")

      major = st.container(border=False)
      with major:
      # Generación fuente hidráulica y combustibles fósiles
        evo_temp_mayor = alt.Chart(gen_mayor).transform_calculate(
        order = "{'Combustible fósil':0, 'Hidráulica':1}[datum.TipoGeneracion]"
        ).mark_line().encode(
          alt.X("Fecha:T").title(None),
          alt.Y("GeneracionRealEstimada:Q").title("[GWh]"),
          alt.Color("TipoGeneracion:N",
                    sort = alt.SortField("order", "ascending"),
                    legend = None
                    # alt.Legend(
                    #   orient = "top",
                    #   legendX = 50,
                    #   legendY = -20,
                    #   direction = 'horizontal',
                    #   titleAnchor = 'middle'
                    # )
                    ,scale = alt.Scale(
                      domain = ['Combustible fósil', 'Hidráulica'],
                      range = ["#e74c3c", "#3498db"])
                    ).title(""),
                  order = "order:O"
          ).interactive(
            bind_y=False,
          ).properties(height=250)

        st.altair_chart(evo_temp_mayor,
                        use_container_width=True)
      
        
      minor = st.container(border=False)
      with minor:
        # Generación fuente solar, biomasa y eólica
        evo_temp_menor = alt.Chart(gen_menor).transform_calculate(
        order = "{'Solar':0, 'Biomasa':1, 'Eólica':2}[datum.TipoGeneracion]"
        ).mark_line().encode(
            alt.X("Fecha:T").title(None),
            alt.Y("GeneracionRealEstimada:Q").title("[GWh]"),
            alt.Color("TipoGeneracion:N",
                      sort = alt.SortField("order", "ascending"),
                      legend=None
                      # alt.Legend(
                      #     orient = 'top',
                      #     legendX = 50,
                      #     legendY = -30,
                      #     direction = 'horizontal',
                      #     titleAnchor = 'middle'
                      #     )
                          , scale= alt.Scale(
                              domain = ['Solar', 'Biomasa', 'Eólica'],
                              range = ["#f39c12", "#2ecc71", "#5D8AA8"])
                          ).title(""),
                      order = "order:O"
        ).interactive(
            bind_y=False
        ).properties(height=250)
        
        st.altair_chart(evo_temp_menor,
                        use_container_width = True)
        
        # --- Tabla ---

        # st.markdown("Top 5 plantas")

        filtro = (generacion["Fecha"] >= pd.to_datetime(fecha_inicial)) & (generacion["Fecha"] <= pd.to_datetime(fecha_final))
          
        if fuente == "Todas" and planta == "Todas":
          filtro = (generacion["Fecha"] >= pd.to_datetime(fecha_inicial)) & (generacion["Fecha"] <= pd.to_datetime(fecha_final))
        else:
          filtro = (generacion["Fecha"] >= pd.to_datetime(fecha_inicial)) & (generacion["Fecha"] <= pd.to_datetime(fecha_final)) & (generacion["NombrePlanta"] == planta)

        generacion = generacion.rename(columns={"NombrePlanta":"Planta",
                                      "GeneracionRealEstimada":"Generación [GWh]",
                                      })
        
        generacion = generacion.loc[filtro].groupby("Planta"
                                          ).sum("Generación [GWh]"
                                          ).sort_values("Generación [GWh]",
                                                        ascending=False
                                          )
        
        generacion["Porcentaje [%]"] = generacion["Generación [GWh]"] / generacion["Generación [GWh]"].sum() * 100

        mayor_gen = st.dataframe(generacion.head(5).round(2),
                                column_config = {
                                  "Generación [GWh]" : "Generación\n [GWh]",
                                  "Porcentaje [%]" : "Porcentaje\n [%]"
                                },
                                hide_index=False)
    
    # Métricas

    with columns[1]:
      col1, col2= st.columns(2,
                            border=False)
      with col1:
          
          filt = generacion_filtrada["TipoGeneracion"]
          filtro_ren = filt != "Combustible fósil"
          filtro_no_ren = filt == "Combustible fósil"
          total = generacion_filtrada["GeneracionRealEstimada"].sum()

          st.metric(label = "% Renovables",
                    value = f"{generacion_filtrada.loc[filtro_ren, "GeneracionRealEstimada"].sum()/total * 100:.2f}",
                    # delta = "-15%",
                    border = True)

      with col2:
          st.metric(label = "% No Renovables",
                    value = f"{generacion_filtrada.loc[filtro_no_ren, "GeneracionRealEstimada"].sum()/total * 100:.2f}",
                    # delta = "-12% ",
                    border = True)

      pie_cont = st.container(border=False)

      with pie_cont:
          # st.subheader("Aportes por fuente")
          
          # Group and sum generation by type
          pie = generacion_filtrada.groupby("TipoGeneracion").sum("GeneracionRealEstimada").reset_index()
          
          # Calculate percentages
          total = pie["GeneracionRealEstimada"].sum()
          pie["percentage"] = (pie["GeneracionRealEstimada"] / total * 100).round(1)
          
          # Define a threshold (e.g., hide if < 5%)
          threshold = 5.0
          pie["label"] = pie["percentage"].apply(lambda p: f"{p}%" if p >= threshold else "")
          
          # Define color order and range
          color_order = ['Hidráulica', 'Combustible fósil', 'Solar', 'Biomasa', 'Eólica']
          color_range = ["#3498db", "#e74c3c", "#f39c12", "#2ecc71", "#5D8AA8"]
          
          # Base chart
          base = alt.Chart(pie).encode(
              theta=alt.Theta("GeneracionRealEstimada:Q", stack=True),
              color=alt.Color(
                  "TipoGeneracion:N",
                  sort=color_order,
                  legend=alt.Legend(orient="bottom", columns=3),
                  scale=alt.Scale(domain=color_order, range=color_range)
              ).title(None)
          )
          
          # 1. Draw arcs
          arcs = base.mark_arc(innerRadius=70)
          
          # 2. Add text labels (only show if percentage >= threshold)
          labels = base.mark_text(
              radius=115,  # Adjust distance from center
              fontSize=12,
              fontWeight="bold",
              color="black"
          ).encode(
              text=alt.Text("label:N")  # Will show empty string for small percentages
          )
          
          # Combine layers
          pie_chart = (arcs + labels).properties(height=300)
          
          st.altair_chart(pie_chart, use_container_width=True)

          # Gráfica de area
          area_acumulada = alt.Chart(generacion_filtrada).transform_calculate(
            order = "{'Hidráulica':0, 'Combustible fósil':1, 'Solar':2, 'Biomasa':3, 'Eólica':4}[datum.TipoGeneracion]"
          ).mark_area().encode(
              x = alt.X("Fecha:T",
                        title = None),
              y = alt.Y("GeneracionRealEstimada:Q",
                    stack = "normalize",
                    title = "Generación [%]"),
              color = alt.Color("TipoGeneracion:N",
                        sort = alt.SortField("order", "descending"),
                        legend=None,
                        scale= alt.Scale(
                                  domain = ['Hidráulica', 'Combustible fósil', 'Solar', 'Biomasa', 'Eólica'],
                                  range=["#3498db", "#e74c3c", "#f39c12", "#2ecc71", "#5D8AA8"])
                            ).title(None),
              order = "order:O",
          ).interactive(
              bind_y=False
          ).properties(height = 280)

          st.altair_chart(area_acumulada,
                          use_container_width=True)
      
      with columns[2]:

        

        fpo = (
          fpo.groupby(
            [pd.Grouper(key = 'Fecha Operación',
                        freq = s),
                        'TipoGeneracion']).agg({'NombrePlanta': 'count'}
              ).reset_index())
          
        fpo = fpo.reset_index(drop=True).rename(columns = {"NombrePlanta": "CantidadPlanta"})
        
        filter = (fpo["TipoGeneracion"] == fuente) & (fpo["Fecha Operación"] >= pd.to_datetime(fecha_inicial)) & (fpo["Fecha Operación"] <= pd.to_datetime(fecha_final))

        if fuente == "Todas":
          filter = (fpo["Fecha Operación"] >= pd.to_datetime(fecha_inicial)) & (fpo["Fecha Operación"] <= pd.to_datetime(fecha_final))
          fpo = fpo.loc[filter]
        else:
          filter = (fpo["TipoGeneracion"] == fuente) & (fpo["Fecha Operación"] >= pd.to_datetime(fecha_inicial)) & (fpo["Fecha Operación"] <= pd.to_datetime(fecha_final))
          fpo = fpo.loc[filter]

        bar = alt.Chart(fpo).transform_calculate(
            order = "{'Hidráulica':0, 'Combustible fósil':1, 'Solar':2, 'Biomasa':3, 'Eólica':4}[datum.TipoGeneracion]"
          ).mark_bar().encode(
          x=alt.X('CantidadPlanta', title = "Cantidad de plantas"),
          y=alt.Y('Fecha Operación', title = "Fecha de puesta en operación"),
          color=alt.Color('TipoGeneracion',
                          sort = alt.SortField("order", "descending"),
                          legend = None,
                          scale= alt.Scale(
                                  domain = ['Hidráulica', 'Combustible fósil', 'Solar', 'Biomasa', 'Eólica'],
                                  range=["#3498db", "#e74c3c", "#f39c12", "#2ecc71", "#5D8AA8"])
                            ).title(None),
                            order = "order:O"
                            ).properties(height=790).interactive(
              bind_x=False
          )

        st.altair_chart(bar,
            use_container_width=True)