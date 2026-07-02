# -*- coding: utf-8 -*-
"""
Script para inserir as campanhas extraídas dos prints.
Semanas 17-21 e 24-28 de Junho de 2026.
"""

import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

campanhas = [
    # Print 1 (1.jpg) — Campanha de alcance local
    # Meta: "Promova sua empresa localmente" | Status: Concluído
    # Alcance: 7.240 | Visualizações: 8.450 | Conversas: 0 (não se aplica, campanha de alcance)
    # Período: 26/06 a 28/06/2026 | Valor total: R$ 13,45
    # Público: Araricá, Da Canoa, Daniel Roque Tolfo | 20 a 45 anos
    {
        'nome_campanha': 'Promova sua empresa localmente - Janta Araricá',
        'publico_alvo': 'Araricá e região - 20 a 45 anos',
        'data_inicio': '2026-06-26',
        'data_fim': '2026-06-28',
        'valor_gasto': 13.45,
        'visualizacoes': 8450,
        'conversas_iniciadas': 0,
        'entregas': 0,
        'observacoes': 'Meta: Promova sua empresa localmente (alcance). Sem conversas por mensagem. Alcance: 7.240.',
    },
    # Print 2 (2.jpg) — Campanha WhatsApp mensagens
    # Meta: "Receber mais mensagens" | Status: Concluído
    # Conversas: 1 | Visualizações: 981 | Alcance: 843
    # Período: 24/06 a 25/06/2026 | Valor total: R$ 10,06
    # Público: Araricá, Da Canoa, Daniel Roque Tolfo | 18 a 65+
    {
        'nome_campanha': 'Receber mais mensagens - Janta Araricá (Quarta/Domingo)',
        'publico_alvo': 'Araricá e região - 18 a 65+',
        'data_inicio': '2026-06-24',
        'data_fim': '2026-06-25',
        'valor_gasto': 10.06,
        'visualizacoes': 981,
        'conversas_iniciadas': 1,
        'entregas': 0,
        'observacoes': 'Meta: Receber mais mensagens no WhatsApp. Alcance: 843. Engajamentos: 400.',
    },
    # Print 3 (3.jpg) — Campanha WhatsApp mensagens
    # Meta: "Receber mais mensagens no WhatsApp" | Status: Concluído
    # Conversas: 2 | Visualizações: 1.142 | Alcance: 975
    # Período: 24/06 a 25/06/2026 | Valor total: R$ 11,01
    # Público: Araricá, Da Canoa, Daniel Roque Tolfo | 18 a 65+
    {
        'nome_campanha': 'Receber mais mensagens WhatsApp - Janta Araricá',
        'publico_alvo': 'Araricá e região - 18 a 65+',
        'data_inicio': '2026-06-24',
        'data_fim': '2026-06-25',
        'valor_gasto': 11.01,
        'visualizacoes': 1142,
        'conversas_iniciadas': 2,
        'entregas': 0,
        'observacoes': 'Meta: Receber mais mensagens no WhatsApp. Alcance: 975. Engajamentos: 13.',
    },
    # Print 4 (4.jpg) — Campanha WhatsApp mensagens (PAUSADA)
    # Meta: "Receber mais mensagens" | Status: Pausado
    # Conversas: 0 (--) | Visualizações: 886 | Alcance: 643
    # Início: 21/06/2026 | Duração: Contínuo | Valor total: R$ 6,55
    # Público: Araricá, Da Canoa, Daniel Roque Tolfo | 18 a 65+
    {
        'nome_campanha': 'Receber mais mensagens - Janta Araricá (Contínuo)',
        'publico_alvo': 'Araricá e região - 18 a 65+',
        'data_inicio': '2026-06-21',
        'data_fim': '2026-06-21',
        'valor_gasto': 6.55,
        'visualizacoes': 886,
        'conversas_iniciadas': 0,
        'entregas': 0,
        'observacoes': 'Status: PAUSADO no mesmo dia de início. Orçamento diário: R$25,00. Engajamentos: 78.',
    },
    # Print 5 (5.jpg) — Campanha WhatsApp mensagens
    # Meta: "Receber mais mensagens" | Status: Concluído
    # Conversas: 1 | Visualizações: 1.288 | Alcance: 1.134
    # Período: 19/06 a 22/06/2026 | Valor total: R$ 14,44
    # Público: Fagundes, Rua Rudolfo Brenner, 649, Araricá | 18 a 65+
    {
        'nome_campanha': 'Receber mais mensagens - Pizza na Mesa (Fagundes)',
        'publico_alvo': 'Fagundes/Araricá - 18 a 65+',
        'data_inicio': '2026-06-19',
        'data_fim': '2026-06-22',
        'valor_gasto': 14.44,
        'visualizacoes': 1288,
        'conversas_iniciadas': 1,
        'entregas': 0,
        'observacoes': 'Meta: Receber mais mensagens. Alcance: 1.134. Engajamentos: 282. Anúncio de pizza com vídeo.',
    },
    # Print 6 (6.jpg) — Campanha WhatsApp mensagens
    # Meta: "Receber mais mensagens" | Status: Concluído
    # Conversas: 7 | Visualizações: 3.586 | Alcance: 2.126
    # Período: 19/06 a 22/06/2026 | Valor total: R$ 26,56
    # Público: Araricá, Da Canoa, Daniel Roque Tolfo | 18 a 65+
    {
        'nome_campanha': 'Receber mais mensagens - Batata Recheada (Araricá)',
        'publico_alvo': 'Araricá e região - 18 a 65+',
        'data_inicio': '2026-06-19',
        'data_fim': '2026-06-22',
        'valor_gasto': 26.56,
        'visualizacoes': 3586,
        'conversas_iniciadas': 7,
        'entregas': 0,
        'observacoes': 'Meta: Receber mais mensagens. Alcance: 2.126. Engajamentos: 690. Anúncio de Batata Recheada a partir de R$45,90.',
    },
]

def inserir_campanhas():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    for c in campanhas:
        cursor.execute('''
            INSERT INTO campanhas 
            (nome_campanha, publico_alvo, data_inicio, data_fim, valor_gasto, 
             visualizacoes, conversas_iniciadas, entregas, observacoes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            c['nome_campanha'],
            c['publico_alvo'],
            c['data_inicio'],
            c['data_fim'],
            c['valor_gasto'],
            c['visualizacoes'],
            c['conversas_iniciadas'],
            c['entregas'],
            c['observacoes'],
        ))
        print(f"  [OK] Inserida: {c['nome_campanha']}")

    conn.commit()
    print(f"\n[INFO] {len(campanhas)} campanhas inseridas com sucesso!")
    
    # Verifica
    total = cursor.execute("SELECT COUNT(*) FROM campanhas").fetchone()[0]
    print(f"[INFO] Total de campanhas no banco: {total}")
    
    conn.close()

if __name__ == '__main__':
    inserir_campanhas()
