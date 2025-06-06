import streamlit as st
import login as login

page_element="""
<style>
[data-testid="stAppViewContainer"]{
  background-image: url("https://cdn.pixabay.com/photo/2018/05/11/22/25/computer-user-3391894_1280.jpg");
  background-size: cover;
}
</style>
"""

st.markdown(page_element, unsafe_allow_html=True)

st.header(':orange[Iniciar] sesión para acceder al Dashboard.')
login.generarLogin()

if 'usuario' in st.session_state:
    st.markdown('# :red[SESIÓN INICIADA]')
    





