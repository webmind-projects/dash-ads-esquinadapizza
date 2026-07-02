# 📊 Processo de Adição de Campanha via AI

Este documento descreve o fluxo de adição de dados de campanha ao dashboard usando assistência de IA, a partir de prints dos resultados das campanhas da Central de Anúncios.

---

## 🔄 Fluxo Completo

### 1. Usuário envia o print da campanha

O usuário envia no chat uma ou mais capturas de tela (prints) dos resultados da campanha, diretamente da Central de Anúncios do aplicativo.

**Informações que devem estar visíveis no print:**
- Nome da campanha
- Público-alvo configurado
- Período de veiculação (data início e data fim)
- Valor gasto (em R$)
- Visualizações
- Conversas iniciadas
- Entregas (se disponível)

> 💡 **Dica:** Se alguma informação não estiver visível no print, o usuário deve informar manualmente no chat.

---

### 2. AI extrai os dados do print

A AI analisa a imagem e extrai os seguintes campos:

| Campo | Tipo | Exemplo |
|-------|------|---------|
| `nome_campanha` | Texto | "Promo Terça da Pizza" |
| `publico_alvo` | Texto | "Zona Sul - 18 a 45 anos" |
| `data_inicio` | Data | 2025-06-16 |
| `data_fim` | Data | 2025-06-22 |
| `valor_gasto` | Decimal (R$) | 150.00 |
| `visualizacoes` | Inteiro | 12500 |
| `conversas_iniciadas` | Inteiro | 87 |
| `entregas` | Inteiro | 34 |
| `observacoes` | Texto (opcional) | "Campanha pausada no dia 20" |

---

### 3. AI confirma os dados com o usuário

Antes de inserir, a AI apresenta os dados extraídos formatados para revisão:

```
📋 Dados extraídos da campanha:

• Nome: Promo Terça da Pizza
• Público-alvo: Zona Sul - 18 a 45 anos
• Período: 16/06/2025 a 22/06/2025
• Valor gasto: R$ 150,00
• Visualizações: 12.500
• Conversas iniciadas: 87
• Entregas: 34
• Observações: —

✅ Confirma a inserção? (sim/não)
```

O usuário revisa e confirma, ou solicita correções.

---

### 4. AI insere os dados no banco

Após confirmação, a AI executa a inserção diretamente no banco SQLite do dashboard:

```python
import sqlite3

conn = sqlite3.connect('database.db')
conn.execute('''
    INSERT INTO campanhas 
    (nome_campanha, publico_alvo, data_inicio, data_fim, valor_gasto, visualizacoes, conversas_iniciadas, entregas, observacoes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    'Promo Terça da Pizza',
    'Zona Sul - 18 a 45 anos',
    '2025-06-16',
    '2025-06-22',
    150.00,
    12500,
    87,
    34,
    None
))
conn.commit()
conn.close()
```

---

### 5. AI confirma a inserção

```
✅ Campanha "Promo Terça da Pizza" inserida com sucesso!

📊 Métricas calculadas:
• Custo por conversa: R$ 1,72
• Custo por entrega: R$ 4,41
• Taxa de conversão: 39,1%
• CPM: R$ 12,00
• Dias ativos: 7
• Gasto médio/dia: R$ 21,43

🔗 Acesse o dashboard para visualizar: http://localhost:5000
```

---

## ✏️ Correções e Edições

Se a AI inserir um dado incorreto, o usuário tem duas opções:

### Opção 1: Corrigir via chat
Basta informar no chat:
> "O valor gasto da campanha 'Promo Terça da Pizza' está errado. O correto é R$ 175,00."

A AI executará o UPDATE no banco.

### Opção 2: Editar pelo dashboard
Acessar a página de edição diretamente:
1. Ir ao dashboard (`/`)
2. Na tabela de campanhas, clicar no botão "Editar" da campanha
3. Corrigir os campos no formulário
4. Salvar

---

## 📝 Modelo de Prompt para Envio

Para facilitar, o usuário pode usar este formato ao enviar dados manualmente (sem print):

```
Nova campanha:
- Nome: [nome da campanha]
- Público: [público-alvo]
- Início: [DD/MM/AAAA]
- Fim: [DD/MM/AAAA]
- Gasto: R$ [valor]
- Visualizações: [número]
- Conversas: [número]
- Entregas: [número]
- Obs: [opcional]
```

---

## ⚠️ Observações Importantes

1. **Sempre confirme os dados** antes de autorizar a inserção — prints podem ter informações cortadas ou ilegíveis.
2. **Mantenha consistência nos nomes de público-alvo** — use os mesmos termos já cadastrados para que os filtros do dashboard funcionem corretamente.
3. **O campo observações é opcional** mas muito útil para registrar pausas, mudanças de configuração, ou contexto relevante da campanha.
4. **Dados duplicados**: Antes de inserir, a AI deve verificar se já existe uma campanha com o mesmo nome e período para evitar duplicatas.
