import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import datetime as dt
import os
import plotly.express as px
import plotly.graph_objects as go
from streamlit_dynamic_filters import DynamicFilters


st.set_page_config(page_title="Sinistro", layout="wide")


if 'pagina_central' not in st.session_state:
    st.session_state.pagina_central = 'home'

def mudar_pagina(nome_pagina):
    st.session_state.pagina_central = nome_pagina

def metricas(df, lista_index, lista_values):
    df = df.pivot_table(index= lista_index,  values= lista_values, aggfunc='sum').reset_index()
    df['CPC'] = df['Valor usado (BRL)'] / df['Cliques no link']
    df['CTR'] = (df['Cliques no link'] / df['Impressões']) * 100
    df['CPM'] = df['Valor usado (BRL)'] / (df['Impressões'] / 1000)
    df['CPL'] = df['Valor usado (BRL)'] / df['Resultados']
    return df

def resultado_campanha(df):
    campanha_list = df['Nome da campanha'].unique().tolist()
    lista = []
    for campanha in campanha_list:
        res = df[(df['Nome da campanha'] == campanha) & (~df['Tipo de resultado'].isna())]['Tipo de resultado'].unique()[0]
        lista.append(res)

    for campanha,resultado in zip(campanha_list,lista):
        df.loc[(df['Nome da campanha'] == campanha) & (df['Tipo de resultado'].isna()),'Tipo de resultado'] = resultado
    return df

def filtros_dinamicos(df):
    dynamic_filters = DynamicFilters(df, ['Tipo de resultado', 'Nome da campanha', 'Nome do conjunto de anúncios', 'Nome do anúncio', 'Status de veiculação'])
    with st.sidebar:
        dynamic_filters.display_filters()
    df_filtrado = dynamic_filters.filter_df()
    indicador = st.sidebar.radio("Indicador", ['Impressões', 'Cliques no link', 'Valor usado (BRL)',"CPC", "CTR", "CPM", 'Resultados', 'CPL'])
    return df_filtrado, indicador
        
def analise_comportamentos(df, indicador):
    if "Idade" in df.columns:
        st.markdown('### Análise de Comportamentos')

        col1, col2 = st.columns(2)

        ###
        ab_idade = metricas(df, ['Idade'], ['Impressões', 'Cliques no link', 'Valor usado (BRL)', 'Resultados'])
        fig = px.bar(ab_idade, x = 'Idade',  y = indicador, 
                        color = 'Idade',
                        title = f'Comparativo de {indicador} por Idade')
        col1.plotly_chart(fig, use_container_width = True)
        ###

        ###
        ab_genero = metricas(df, ['Gênero'], ['Impressões', 'Cliques no link', 'Valor usado (BRL)', 'Resultados'])
        fig2 = px.bar(ab_genero, x = 'Gênero',  y = indicador, 
                        color = 'Gênero',
                        title = f'Comparativo de {indicador} por Gênero')
        col2.plotly_chart(fig2, use_container_width = True)
        ###

        ###
        ab_genero = metricas(df, ['Gênero', 'Idade'], ['Impressões', 'Cliques no link', 'Valor usado (BRL)', 'Resultados'])
        fig2 = px.density_heatmap(ab_genero, x =  'Idade', y = 'Gênero', z = indicador,
                        title = f'Comparativo de {indicador} por Idade e Gênero')
        st.plotly_chart(fig2, use_container_width = True)
        ###
 
def home():

    st.markdown("# Marketing Analytics")
    st.divider()
    st.sidebar.markdown("# Filtros")
    st.text("Insira abaixo o arquivo em Excel (.xlsx) com os dados da campanha.")
    file = st.file_uploader("Escolha um arquivo", type="xlsx")

    if file is not None:
        df = pd.read_excel(file)
        df['Dia'] = pd.to_datetime(df['Dia'], infer_datetime_format= True).dt.date

        st.divider()
        
        df = resultado_campanha(df)
        st.write(df.head())
        df_filtrado, indicador = filtros_dinamicos(df)

        ######### Indicadores
        impressoes = df_filtrado['Impressões'].sum()
        cliques = df_filtrado['Cliques no link'].sum()
        ctr = '{:.2f}%'.format((cliques / impressoes) * 100)
        valor_usado = df_filtrado['Valor usado (BRL)'].sum()
        cpc = valor_usado / cliques
        cpm = valor_usado / (impressoes / 1000)
        avg_freq = df_filtrado['Frequência'].mean()
        resultado = df_filtrado['Resultados'].sum()

        st.markdown("### Resumo da Campanha")

        col1, col2, col3 = st.columns(3)

        #Linha 1
        col1.metric("Impressões", value = impressoes)
        col2.metric("Cliques", value = cliques)
        col3.metric("(%) CTR", value = ctr)

        #Linha 2
        col1.metric("Valor Usado (BRL)", value = 'R${:.2f}'.format(valor_usado.round(2)))
        col2.metric("Custo por Clique", value = 'R${:.2f}'.format(cpc.round(2)))
        col3.metric("Resultados", value = df_filtrado['Resultados'].sum().round(2))

        #Linha 3
        col1.metric("CPM", value = 'R${:.2f}'.format(cpm.round(2)))
        col2.metric("CPL", value = (df_filtrado['Valor usado (BRL)'].sum() / df_filtrado['Resultados'].sum()).round(2))
        col3.metric("Frequência Média", value = avg_freq.round(2))

        ###
        st.markdown('##### Série Temporal de Indicadores')
        df_st = metricas(df_filtrado, ['Dia'] , ['Impressões', 'Cliques no link', 'Valor usado (BRL)', 'Resultados'])
        st.line_chart(data = df_st, x = 'Dia', y = indicador)
        ###

        ###
        st.markdown('### Análise de Campanhas')
        col1, col2 = st.columns(2)
        st_campanha = metricas(df_filtrado, ['Dia', 'Nome da campanha'], ['Impressões', 'Cliques no link', 'Valor usado (BRL)', 'Resultados'])
        fig = px.line(st_campanha, x = 'Dia',  y = indicador, 
                      line_group= 'Nome da campanha', 
                      color = 'Nome da campanha',
                      title = 'Série Temporal de Indicadores por Campanha')
        col1.plotly_chart(fig.update_layout(showlegend = False), use_container_width = True)    
        ###

        ###
        ab_campanha = metricas(df_filtrado, ['Nome da campanha'], ['Impressões', 'Cliques no link', 'Valor usado (BRL)', 'Resultados'])
        fig2 = px.bar(ab_campanha, x = 'Nome da campanha',  y = indicador, 
                      color = 'Nome da campanha',
                      title = 'Comparativo de Indicadores por Campanha')
        col2.plotly_chart(fig2, use_container_width = True)    
        st.divider()
        ###

        ###
        st.markdown('### Análise de Conjuntos de Anúncios')
        col1, col2 = st.columns(2)
        st_conjuntos = metricas(df_filtrado, ['Dia', 'Nome do conjunto de anúncios'], ['Impressões', 'Cliques no link', 'Valor usado (BRL)', 'Resultados'])
        fig = px.line(st_conjuntos, x = 'Dia',  y = indicador, 
                      line_group= 'Nome do conjunto de anúncios', 
                      color = 'Nome do conjunto de anúncios',
                      title = 'Série Temporal de Indicadores por Campanha')
        col1.plotly_chart(fig.update_layout(showlegend = False), use_container_width = True)    
        ###

        ###
        ab_conjuntos = metricas(df_filtrado, ['Nome do conjunto de anúncios'], ['Impressões', 'Cliques no link', 'Valor usado (BRL)', 'Resultados'])
        fig2 = px.bar(ab_conjuntos, x = 'Nome do conjunto de anúncios',  y = indicador, 
                      color = 'Nome do conjunto de anúncios',
                      title = 'Comparativo de Indicadores por Campanha')
        col2.plotly_chart(fig2, use_container_width = True)    
        st.divider()
        ###

        analise_comportamentos(df_filtrado, indicador)

    else: 
        st.text("Arquivo não processado ainda.")
    

def main():

    if st.session_state.pagina_central == 'home':
        home()

main()



