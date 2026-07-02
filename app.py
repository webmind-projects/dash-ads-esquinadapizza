# -*- coding: utf-8 -*-
"""
app.py — Aplicação Flask principal do Dashboard Esquina da Pizza.

Rotas, processamento de dados com Pandas e geração de gráficos Plotly.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from database import get_db, close_db, init_db
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime, timedelta, date
import locale
import os

# Tenta configurar locale brasileiro para formatação
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except locale.Error:
        pass

# ============================================================
# CONFIGURAÇÃO DO APP
# ============================================================

app = Flask(__name__)
app.secret_key = 'esquina-da-pizza-dashboard-2025'

# Paleta de cores da marca (extraída da logo)
CORES = {
    'vermelho': '#C41E3A',
    'vermelho_escuro': '#a01830',
    'verde': '#2D8B2D',
    'verde_escuro': '#246e24',
    'dourado': '#D4A843',
    'dourado_escuro': '#b8923a',
    'laranja': '#e07828',
    'fundo': '#0a0a0a',
    'card': '#141414',
    'borda': '#2a2a2a',
    'texto': '#f0f0f0',
    'texto_secundario': '#999999',
}

# Layout base Plotly para tema dark
PLOTLY_LAYOUT_BASE = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(
        family='Inter, sans-serif',
        color=CORES['texto'],
        size=13,
    ),
    margin=dict(l=40, r=20, t=40, b=40),
    hoverlabel=dict(
        bgcolor=CORES['card'],
        bordercolor=CORES['borda'],
        font=dict(family='Inter, sans-serif', color=CORES['texto'], size=13),
    ),
    showlegend=True,
    legend=dict(
        bgcolor='rgba(0,0,0,0)',
        bordercolor='rgba(0,0,0,0)',
        font=dict(color=CORES['texto_secundario'], size=11),
    ),
)


# ============================================================
# HELPERS — Formatação
# ============================================================

def formatar_moeda(valor):
    """Formata valor como moeda brasileira: R$ 1.234,56"""
    if valor is None or pd.isna(valor):
        return 'R$ 0,00'
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def formatar_numero(valor):
    """Formata número inteiro com separador de milhar brasileiro."""
    if valor is None or pd.isna(valor):
        return '0'
    return f"{int(valor):,}".replace(',', '.')


def formatar_percentual(valor):
    """Formata valor como percentual brasileiro."""
    if valor is None or pd.isna(valor):
        return '0,0%'
    return f"{valor:.1f}%".replace('.', ',')


def gerar_codigo_campanha(letra, data_inicio_str, data_fim_str):
    """
    Gera código curto no formato LetraDD-DD.
    Ex: A21-25  (letra A, início dia 21, fim dia 25)
    A letra é normalizada para maiúsculo e apenas 1 caractere.
    """
    letra = (letra or 'A').strip().upper()[:1] or 'A'
    try:
        dia_ini = datetime.strptime(data_inicio_str, '%Y-%m-%d').day
        dia_fim = datetime.strptime(data_fim_str, '%Y-%m-%d').day
        return f"{letra}{dia_ini:02d}-{dia_fim:02d}"
    except (ValueError, TypeError):
        return f"{letra}??-??"


# ============================================================
# HELPERS — Banco de Dados
# ============================================================

def obter_campanhas_filtradas(periodo=None, data_inicio_custom=None, data_fim_custom=None, publico=None):
    """
    Busca campanhas no banco com filtros opcionais de período e público-alvo.
    Retorna um DataFrame Pandas com as campanhas filtradas.
    """
    conn = get_db()

    query = "SELECT * FROM campanhas WHERE 1=1"
    params = []

    # Filtro de período
    hoje = date.today()
    if periodo == 'hoje':
        query += " AND data_inicio <= ? AND data_fim >= ?"
        params.extend([hoje.isoformat(), hoje.isoformat()])
    elif periodo == 'semana_atual':
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        fim_semana = inicio_semana + timedelta(days=6)
        query += " AND data_fim >= ? AND data_inicio <= ?"
        params.extend([inicio_semana.isoformat(), fim_semana.isoformat()])
    elif periodo == 'semana_passada':
        inicio_semana_passada = hoje - timedelta(days=hoje.weekday() + 7)
        fim_semana_passada = inicio_semana_passada + timedelta(days=6)
        query += " AND data_fim >= ? AND data_inicio <= ?"
        params.extend([inicio_semana_passada.isoformat(), fim_semana_passada.isoformat()])
    elif periodo == 'custom' and data_inicio_custom and data_fim_custom:
        query += " AND data_fim >= ? AND data_inicio <= ?"
        params.extend([data_inicio_custom, data_fim_custom])

    # Filtro de público-alvo
    if publico and publico != 'todos':
        query += " AND publico_alvo = ?"
        params.append(publico)

    query += " ORDER BY data_inicio DESC"

    df = pd.read_sql_query(query, conn, params=params)
    close_db(conn)

    return df


def calcular_metricas(df):
    """
    Calcula métricas derivadas a partir do DataFrame de campanhas.
    Retorna o DataFrame com colunas adicionais de métricas.
    """
    if df.empty:
        return df

    # Converte datas
    df['data_inicio'] = pd.to_datetime(df['data_inicio'])
    df['data_fim'] = pd.to_datetime(df['data_fim'])

    # Métricas calculadas (com proteção contra divisão por zero)
    df['custo_por_conversa'] = df.apply(
        lambda r: r['valor_gasto'] / r['conversas_iniciadas'] if r['conversas_iniciadas'] > 0 else 0, axis=1
    )
    df['cpm'] = df.apply(
        lambda r: (r['valor_gasto'] / r['visualizacoes']) * 1000 if r['visualizacoes'] > 0 else 0, axis=1
    )
    df['dias_ativos'] = (df['data_fim'] - df['data_inicio']).dt.days + 1
    df['gasto_medio_dia'] = df.apply(
        lambda r: r['valor_gasto'] / r['dias_ativos'] if r['dias_ativos'] > 0 else 0, axis=1
    )

    return df


# ============================================================
# HELPERS — Gráficos Plotly
# ============================================================

def gerar_grafico_funil(df):
    """Gera gráfico de funil: Visualizações → Conversas."""
    total_vis = int(df['visualizacoes'].sum())
    total_conv = int(df['conversas_iniciadas'].sum())

    # Divide views por 100 para proporção realista no funil
    vis_100x = round(total_vis / 100, 1) if total_vis > 0 else 0

    fig = go.Figure(go.Funnel(
        y=['Visto 100x', 'Conversas'],
        x=[vis_100x, total_conv],
        text=[
            f'{vis_100x:,.2f}x ({formatar_numero(total_vis)})',
            f'{formatar_numero(total_conv)} conversas'
        ],
        textinfo='text+percent initial',
        textfont=dict(size=13, family='Inter, sans-serif'),
        marker=dict(
            color=[CORES['dourado'], CORES['vermelho']],
            line=dict(width=1, color=CORES['borda']),
        ),
        connector=dict(
            line=dict(color=CORES['borda'], width=1),
            fillcolor='rgba(42, 42, 42, 0.3)',
        ),
        textposition='auto',
    ))

    layout = {**PLOTLY_LAYOUT_BASE}
    layout.update(
        title=None,
        showlegend=False,
        height=380,
    )
    fig.update_layout(**layout)

    return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={'responsive': True, 'displayModeBar': False})


def gerar_grafico_barras(df):
    """Gera gráfico de barras comparando campanhas: Gasto e Conversas."""
    # Limita a 15 campanhas para legibilidade
    df_plot = df.head(15).sort_values('data_inicio').copy()

    # Usa o código curto como label; se vazio, usa o ID numérico
    df_plot['label'] = df_plot.apply(
        lambda r: r['codigo_campanha'] if pd.notna(r.get('codigo_campanha')) and str(r.get('codigo_campanha', '')).strip()
        else f"#{int(r['id'])}",
        axis=1
    )
    df_plot['hover_nome'] = df_plot['nome_campanha']

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Gasto (R$)',
        x=df_plot['label'],
        y=df_plot['valor_gasto'],
        marker_color=CORES['vermelho'],
        marker_line=dict(width=0),
        customdata=df_plot['hover_nome'],
        hovertemplate='<b>%{customdata}</b><br>Gasto: R$ %{y:,.2f}<extra></extra>',
        opacity=0.9,
    ))

    fig.add_trace(go.Bar(
        name='Conversas',
        x=df_plot['label'],
        y=df_plot['conversas_iniciadas'],
        marker_color=CORES['dourado'],
        marker_line=dict(width=0),
        customdata=df_plot['hover_nome'],
        hovertemplate='<b>%{customdata}</b><br>Conversas: %{y}<extra></extra>',
        opacity=0.9,
    ))

    layout = {**PLOTLY_LAYOUT_BASE}
    layout.update(
        title=None,
        barmode='group',
        height=400,
        xaxis=dict(
            tickangle=0,
            gridcolor='rgba(42, 42, 42, 0.5)',
            showgrid=False,
            tickfont=dict(size=12),
        ),
        yaxis=dict(
            gridcolor='rgba(42, 42, 42, 0.5)',
            showgrid=True,
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
        ),
    )
    fig.update_layout(**layout)

    return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={'responsive': True, 'displayModeBar': False})


def gerar_grafico_linha(df, df_entregas=None):
    """Gera gráfico de linha: tendência semanal de campanhas + entregas diárias."""
    if df.empty or len(df) < 2:
        return None

    # Agrupa campanhas por semana (data_inicio)
    df_temp = df.copy()
    df_temp['semana'] = df_temp['data_inicio'].dt.to_period('W').apply(lambda r: r.start_time)

    semanal = df_temp.groupby('semana').agg({
        'valor_gasto': 'sum',
        'visualizacoes': 'sum',
        'conversas_iniciadas': 'sum',
    }).reset_index()

    semanal = semanal.sort_values('semana')

    if len(semanal) < 2:
        return None

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        name='Gasto (R$)',
        x=semanal['semana'],
        y=semanal['valor_gasto'],
        mode='lines+markers',
        line=dict(color=CORES['vermelho'], width=2.5),
        marker=dict(size=7, symbol='circle'),
        hovertemplate='<b>Semana de %{x|%d/%m}</b><br>Gasto: R$ %{y:,.2f}<extra></extra>',
    ))

    fig.add_trace(go.Scatter(
        name='Conversas (anúncios)',
        x=semanal['semana'],
        y=semanal['conversas_iniciadas'],
        mode='lines+markers',
        line=dict(color=CORES['dourado'], width=2.5),
        marker=dict(size=7, symbol='diamond'),
        yaxis='y2',
        hovertemplate='<b>Semana de %{x|%d/%m}</b><br>Conversas: %{y}<extra></extra>',
    ))

    # Overlay de entregas diárias (agrupadas por semana)
    if df_entregas is not None and not df_entregas.empty:
        df_ent = df_entregas.copy()
        df_ent['data'] = pd.to_datetime(df_ent['data'])
        df_ent['semana'] = df_ent['data'].dt.to_period('W').apply(lambda r: r.start_time)
        semanal_ent = df_ent.groupby('semana').agg({'quantidade': 'sum'}).reset_index()
        semanal_ent = semanal_ent.sort_values('semana')

        fig.add_trace(go.Scatter(
            name='Entregas (pizzaria)',
            x=semanal_ent['semana'],
            y=semanal_ent['quantidade'],
            mode='lines+markers',
            line=dict(color=CORES['verde'], width=2.5, dash='dot'),
            marker=dict(size=8, symbol='square'),
            yaxis='y2',
            hovertemplate='<b>Semana de %{x|%d/%m}</b><br>Entregas: %{y}<extra></extra>',
        ))

    layout = {**PLOTLY_LAYOUT_BASE}
    layout.update(
        title=None,
        height=400,
        xaxis=dict(
            gridcolor='rgba(42, 42, 42, 0.5)',
            showgrid=True,
            tickformat='%d/%m',
        ),
        yaxis=dict(
            title='Gasto (R$)',
            title_font=dict(color=CORES['vermelho']),
            tickfont=dict(color=CORES['vermelho']),
            gridcolor='rgba(42, 42, 42, 0.5)',
            showgrid=True,
        ),
        yaxis2=dict(
            title='Quantidade',
            title_font=dict(color=CORES['dourado']),
            tickfont=dict(color=CORES['dourado']),
            overlaying='y',
            side='right',
            showgrid=False,
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
        ),
    )
    fig.update_layout(**layout)

    return pio.to_html(fig, full_html=False, include_plotlyjs=False, config={'responsive': True, 'displayModeBar': False})


# ============================================================
# HELPERS — Entregas Diárias
# ============================================================

def obter_datas_periodo(periodo, data_inicio_custom=None, data_fim_custom=None):
    """Converte o filtro de período em um intervalo de datas (start, end) como strings ISO."""
    hoje = date.today()
    if periodo == 'hoje':
        return hoje.isoformat(), hoje.isoformat()
    elif periodo == 'semana_atual':
        inicio = hoje - timedelta(days=hoje.weekday())
        fim = inicio + timedelta(days=6)
        return inicio.isoformat(), fim.isoformat()
    elif periodo == 'semana_passada':
        inicio = hoje - timedelta(days=hoje.weekday() + 7)
        fim = inicio + timedelta(days=6)
        return inicio.isoformat(), fim.isoformat()
    elif periodo == 'custom' and data_inicio_custom and data_fim_custom:
        return data_inicio_custom, data_fim_custom
    return None, None  # todos


def obter_entregas_periodo(data_inicio=None, data_fim=None):
    """Retorna DataFrame de entregas_diarias filtrado pelo período."""
    conn = get_db()
    query = "SELECT * FROM entregas_diarias WHERE 1=1"
    params = []
    if data_inicio:
        query += " AND data >= ?"
        params.append(data_inicio)
    if data_fim:
        query += " AND data <= ?"
        params.append(data_fim)
    query += " ORDER BY data"
    df = pd.read_sql_query(query, conn, params=params)
    close_db(conn)
    return df


def obter_entregas_recentes(n=7):
    """Retorna os últimos n registros de entregas_diarias para o painel rápido."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM entregas_diarias ORDER BY data DESC LIMIT ?", (n,)
    ).fetchall()
    close_db(conn)
    resultado = []
    for r in rows:
        d = dict(r)
        try:
            d['data_fmt'] = datetime.strptime(d['data'], '%Y-%m-%d').strftime('%d/%m')
        except Exception:
            d['data_fmt'] = d['data']
        resultado.append(d)
    return resultado


# ============================================================
# ROTAS
# ============================================================

@app.route('/')
def dashboard():
    """Página principal — Dashboard com KPIs, gráficos e tabela."""
    # Obtém parâmetros de filtro
    periodo = request.args.get('periodo', 'todos')
    publico = request.args.get('publico', 'todos')
    data_inicio_custom = request.args.get('data_inicio', '')
    data_fim_custom = request.args.get('data_fim', '')

    # Busca campanhas filtradas
    df = obter_campanhas_filtradas(
        periodo=periodo,
        data_inicio_custom=data_inicio_custom,
        data_fim_custom=data_fim_custom,
        publico=publico,
    )

    # Calcula métricas
    df = calcular_metricas(df)

    # Entregas diárias independentes (nova lógica)
    data_ini_ent, data_fim_ent = obter_datas_periodo(periodo, data_inicio_custom, data_fim_custom)
    df_entregas = obter_entregas_periodo(data_ini_ent, data_fim_ent)

    # KPIs agregados
    kpis = {
        'total_investido': float(df['valor_gasto'].sum()) if not df.empty else 0,
        'total_visualizacoes': int(df['visualizacoes'].sum()) if not df.empty else 0,
        'total_conversas': int(df['conversas_iniciadas'].sum()) if not df.empty else 0,
        'total_entregas': int(df_entregas['quantidade'].sum()) if not df_entregas.empty else 0,
        'custo_por_conversa_geral': 0,
    }

    total_conv = kpis['total_conversas']
    if total_conv > 0:
        kpis['custo_por_conversa_geral'] = kpis['total_investido'] / total_conv

    # Gráficos (somente se houver dados)
    grafico_funil = gerar_grafico_funil(df) if not df.empty else None
    grafico_barras = gerar_grafico_barras(df) if not df.empty else None
    grafico_linha = gerar_grafico_linha(df, df_entregas) if not df.empty else None

    # Últimos 7 registros de entregas para painel rápido
    entregas_recentes = obter_entregas_recentes(7)

    # Prepara dados da tabela com formatação
    tabela = []
    if not df.empty:
        for _, row in df.iterrows():
            tabela.append({
                'id': int(row['id']),
                'codigo_campanha': row.get('codigo_campanha') or '',
                'nome_campanha': row['nome_campanha'],
                'publico_alvo': row['publico_alvo'],
                'link_anuncio': row.get('link_anuncio') or '',
                'data_inicio': row['data_inicio'].strftime('%d/%m/%Y'),
                'data_fim': row['data_fim'].strftime('%d/%m/%Y'),
                'valor_gasto': formatar_moeda(row['valor_gasto']),
                'valor_gasto_raw': float(row['valor_gasto']),
                'visualizacoes': formatar_numero(row['visualizacoes']),
                'visualizacoes_raw': int(row['visualizacoes']),
                'conversas_iniciadas': formatar_numero(row['conversas_iniciadas']),
                'conversas_raw': int(row['conversas_iniciadas']),
                'custo_por_conversa': formatar_moeda(row['custo_por_conversa']),
                'cpm': formatar_moeda(row['cpm']),
                'dias_ativos': int(row['dias_ativos']),
                'gasto_medio_dia': formatar_moeda(row['gasto_medio_dia']),
                'observacoes': row['observacoes'] or '',
            })

    # Lista de públicos-alvo para o filtro
    conn = get_db()
    publicos = [row['publico_alvo'] for row in conn.execute(
        "SELECT DISTINCT publico_alvo FROM campanhas ORDER BY publico_alvo"
    ).fetchall()]
    close_db(conn)

    return render_template('dashboard.html',
        kpis=kpis,
        grafico_funil=grafico_funil,
        grafico_barras=grafico_barras,
        grafico_linha=grafico_linha,
        tabela=tabela,
        publicos=publicos,
        filtro_periodo=periodo,
        filtro_publico=publico,
        filtro_data_inicio=data_inicio_custom,
        filtro_data_fim=data_fim_custom,
        formatar_moeda=formatar_moeda,
        formatar_numero=formatar_numero,
        formatar_percentual=formatar_percentual,
        entregas_recentes=entregas_recentes,
        hoje=date.today().isoformat(),
    )


@app.route('/nova-campanha', methods=['GET', 'POST'])
def nova_campanha():
    """Página de cadastro de nova campanha."""
    if request.method == 'POST':
        # Coleta dados do formulário
        nome = request.form.get('nome_campanha', '').strip()
        publico = request.form.get('publico_alvo', '').strip()
        data_inicio = request.form.get('data_inicio', '').strip()
        data_fim = request.form.get('data_fim', '').strip()
        valor_gasto = request.form.get('valor_gasto', '').strip()
        visualizacoes = request.form.get('visualizacoes', '').strip()
        conversas = request.form.get('conversas_iniciadas', '').strip()
        link_anuncio = request.form.get('link_anuncio', '').strip() or None
        observacoes = request.form.get('observacoes', '').strip() or None
        codigo_letra = request.form.get('codigo_letra', '').strip()
        codigo_campanha = request.form.get('codigo_campanha', '').strip() or None

        # Validações
        erros = []
        if not nome:
            erros.append('Nome da campanha é obrigatório.')
        if not publico:
            erros.append('Público-alvo é obrigatório.')
        if not data_inicio:
            erros.append('Data de início é obrigatória.')
        if not data_fim:
            erros.append('Data de fim é obrigatória.')

        # Valida datas
        try:
            dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date() if data_inicio else None
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d').date() if data_fim else None
            if dt_inicio and dt_fim and dt_fim < dt_inicio:
                erros.append('Data de fim deve ser igual ou posterior à data de início.')
        except ValueError:
            erros.append('Formato de data inválido.')

        # Valida numéricos
        try:
            valor_gasto_num = float(valor_gasto) if valor_gasto else None
            if valor_gasto_num is None or valor_gasto_num < 0:
                erros.append('Valor gasto deve ser um número positivo.')
        except ValueError:
            erros.append('Valor gasto inválido.')
            valor_gasto_num = None

        try:
            visualizacoes_num = int(visualizacoes) if visualizacoes else None
            if visualizacoes_num is None or visualizacoes_num < 0:
                erros.append('Visualizações deve ser um número inteiro positivo.')
        except ValueError:
            erros.append('Visualizações inválido.')
            visualizacoes_num = None

        try:
            conversas_num = int(conversas) if conversas else None
            if conversas_num is None or conversas_num < 0:
                erros.append('Conversas iniciadas deve ser um número inteiro positivo.')
        except ValueError:
            erros.append('Conversas iniciadas inválido.')
            conversas_num = None

        if erros:
            for erro in erros:
                flash(erro, 'error')
            # Retorna o formulário com os dados preenchidos
            return render_template('nova_campanha.html',
                form_data=request.form,
                publicos=_obter_publicos(),
            )

        # Gera código automaticamente se não foi informado manualmente
        if not codigo_campanha:
            codigo_campanha = gerar_codigo_campanha(codigo_letra or 'A', data_inicio, data_fim)

        # Insere no banco
        conn = get_db()
        conn.execute('''
            INSERT INTO campanhas 
            (codigo_campanha, nome_campanha, publico_alvo, data_inicio, data_fim, valor_gasto, 
             visualizacoes, conversas_iniciadas, link_anuncio, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (codigo_campanha, nome, publico, data_inicio, data_fim, valor_gasto_num,
              visualizacoes_num, conversas_num, link_anuncio, observacoes))
        conn.commit()
        close_db(conn)

        flash(f'Campanha "{nome}" ({codigo_campanha}) cadastrada com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('nova_campanha.html',
        form_data={},
        publicos=_obter_publicos(),
    )


@app.route('/editar-campanha/<int:campanha_id>', methods=['GET', 'POST'])
def editar_campanha(campanha_id):
    """Página de edição de campanha existente."""
    conn = get_db()

    if request.method == 'POST':
        # Coleta dados do formulário
        nome = request.form.get('nome_campanha', '').strip()
        publico = request.form.get('publico_alvo', '').strip()
        data_inicio = request.form.get('data_inicio', '').strip()
        data_fim = request.form.get('data_fim', '').strip()
        valor_gasto = request.form.get('valor_gasto', '').strip()
        visualizacoes = request.form.get('visualizacoes', '').strip()
        conversas = request.form.get('conversas_iniciadas', '').strip()
        link_anuncio = request.form.get('link_anuncio', '').strip() or None
        observacoes = request.form.get('observacoes', '').strip() or None
        codigo_campanha = request.form.get('codigo_campanha', '').strip() or None

        # Validações (mesmas da criação)
        erros = []
        if not nome:
            erros.append('Nome da campanha é obrigatório.')
        if not publico:
            erros.append('Público-alvo é obrigatório.')
        if not data_inicio or not data_fim:
            erros.append('Datas são obrigatórias.')

        try:
            dt_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date() if data_inicio else None
            dt_fim = datetime.strptime(data_fim, '%Y-%m-%d').date() if data_fim else None
            if dt_inicio and dt_fim and dt_fim < dt_inicio:
                erros.append('Data de fim deve ser igual ou posterior à data de início.')
        except ValueError:
            erros.append('Formato de data inválido.')

        try:
            valor_gasto_num = float(valor_gasto) if valor_gasto else 0
        except ValueError:
            erros.append('Valor gasto inválido.')
            valor_gasto_num = 0

        try:
            visualizacoes_num = int(visualizacoes) if visualizacoes else 0
        except ValueError:
            erros.append('Visualizações inválido.')
            visualizacoes_num = 0

        try:
            conversas_num = int(conversas) if conversas else 0
        except ValueError:
            erros.append('Conversas iniciadas inválido.')
            conversas_num = 0

        if erros:
            for erro in erros:
                flash(erro, 'error')
            close_db(conn)
            return render_template('editar_campanha.html',
                campanha=request.form,
                campanha_id=campanha_id,
                publicos=_obter_publicos(),
            )

        # Se código não foi informado, gera automaticamente
        if not codigo_campanha:
            codigo_campanha = gerar_codigo_campanha('A', data_inicio, data_fim)

        # Atualiza no banco
        conn.execute('''
            UPDATE campanhas SET
                codigo_campanha = ?, nome_campanha = ?, publico_alvo = ?, data_inicio = ?, data_fim = ?,
                valor_gasto = ?, visualizacoes = ?, conversas_iniciadas = ?,
                link_anuncio = ?, observacoes = ?
            WHERE id = ?
        ''', (codigo_campanha, nome, publico, data_inicio, data_fim, valor_gasto_num,
              visualizacoes_num, conversas_num, link_anuncio, observacoes, campanha_id))
        conn.commit()
        close_db(conn)

        flash(f'Campanha "{nome}" ({codigo_campanha}) atualizada com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    # GET — carrega dados existentes
    campanha = conn.execute("SELECT * FROM campanhas WHERE id = ?", (campanha_id,)).fetchone()
    close_db(conn)

    if not campanha:
        flash('Campanha não encontrada.', 'error')
        return redirect(url_for('dashboard'))

    return render_template('editar_campanha.html',
        campanha=dict(campanha),
        campanha_id=campanha_id,
        publicos=_obter_publicos(),
    )


@app.route('/excluir-campanha/<int:campanha_id>', methods=['POST'])
def excluir_campanha(campanha_id):
    """Exclui uma campanha pelo ID."""
    conn = get_db()
    campanha = conn.execute("SELECT nome_campanha FROM campanhas WHERE id = ?", (campanha_id,)).fetchone()

    if campanha:
        conn.execute("DELETE FROM campanhas WHERE id = ?", (campanha_id,))
        conn.commit()
        flash(f'Campanha "{campanha["nome_campanha"]}" excluída com sucesso.', 'success')
    else:
        flash('Campanha não encontrada.', 'error')

    close_db(conn)
    return redirect(url_for('dashboard'))


@app.route('/api/publicos')
def api_publicos():
    """API JSON — retorna lista de públicos-alvo cadastrados."""
    return jsonify(_obter_publicos())


@app.route('/registrar-entrega', methods=['POST'])
def registrar_entrega():
    """Registra ou atualiza a contagem de entregas de um dia específico."""
    data_entrega = request.form.get('data_entrega', '').strip()
    quantidade = request.form.get('quantidade_entregas', '').strip()
    obs = request.form.get('obs_entregas', '').strip() or None

    if not data_entrega or not quantidade:
        flash('Data e quantidade são obrigatórias.', 'error')
        return redirect(url_for('dashboard'))

    try:
        qtd = int(quantidade)
        if qtd < 0:
            raise ValueError
    except ValueError:
        flash('Quantidade de entregas inválida.', 'error')
        return redirect(url_for('dashboard'))

    conn = get_db()
    # UPSERT — se já existe registro para o dia, atualiza
    conn.execute('''
        INSERT INTO entregas_diarias (data, quantidade, observacoes)
        VALUES (?, ?, ?)
        ON CONFLICT(data) DO UPDATE SET
            quantidade = excluded.quantidade,
            observacoes = excluded.observacoes
    ''', (data_entrega, qtd, obs))
    conn.commit()
    close_db(conn)

    try:
        data_fmt = datetime.strptime(data_entrega, '%Y-%m-%d').strftime('%d/%m/%Y')
    except Exception:
        data_fmt = data_entrega

    flash(f'{qtd} entregas registradas para {data_fmt}.', 'success')
    return redirect(url_for('dashboard'))


def _obter_publicos():
    """Helper: retorna lista de públicos-alvo distintos."""
    conn = get_db()
    publicos = [row['publico_alvo'] for row in conn.execute(
        "SELECT DISTINCT publico_alvo FROM campanhas ORDER BY publico_alvo"
    ).fetchall()]
    close_db(conn)
    return publicos


# ============================================================
# INICIALIZAÇÃO
# ============================================================

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
