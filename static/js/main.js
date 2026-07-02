/**
 * main.js — Dashboard Esquina da Pizza
 * 
 * Funcionalidades:
 * - Contagem progressiva animada nos KPIs
 * - Filtros com submit automático
 * - Tabela ordenável por coluna
 * - Confirmação de exclusão
 * - Animações de entrada via Intersection Observer
 */

// ============================================================
// CONTAGEM PROGRESSIVA (Count-Up) nos Cards de KPI
// ============================================================

/**
 * Formata número no padrão brasileiro.
 * @param {number} value - Valor numérico
 * @param {string} type - Tipo de formatação: 'moeda', 'percentual', 'inteiro'
 * @returns {string} Valor formatado
 */
function formatarNumero(value, type) {
    if (type === 'moeda') {
        return 'R$ ' + value.toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    } else if (type === 'percentual') {
        return value.toLocaleString('pt-BR', {
            minimumFractionDigits: 1,
            maximumFractionDigits: 1
        }) + '%';
    } else {
        // Inteiro com separador de milhar
        return value.toLocaleString('pt-BR', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
    }
}

/**
 * Anima a contagem de 0 até o valor alvo em um elemento.
 * @param {HTMLElement} element - Elemento com data-target e data-type
 * @param {number} duration - Duração da animação em ms
 */
function countUp(element, duration = 1500) {
    const target = parseFloat(element.dataset.target) || 0;
    const type = element.dataset.type || 'inteiro';
    const startTime = performance.now();

    // Easing function (ease-out cubic)
    function easeOutCubic(t) {
        return 1 - Math.pow(1 - t, 3);
    }

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easedProgress = easeOutCubic(progress);
        const currentValue = target * easedProgress;

        element.textContent = formatarNumero(currentValue, type);

        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            // Garante o valor final exato
            element.textContent = formatarNumero(target, type);
        }
    }

    requestAnimationFrame(update);
}

// ============================================================
// INTERSECTION OBSERVER — Animações ao rolar
// ============================================================

/**
 * Configura o Intersection Observer para disparar animações
 * quando elementos entram na viewport.
 */
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');

                // Se for um elemento de contagem, inicia a animação
                if (entry.target.classList.contains('kpi-value')) {
                    countUp(entry.target);
                }

                // Observa apenas uma vez
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observa cards KPI
    document.querySelectorAll('.kpi-card').forEach(card => {
        observer.observe(card);
    });

    // Observa valores KPI para contagem
    document.querySelectorAll('.kpi-value').forEach(value => {
        observer.observe(value);
    });

    // Observa seções de gráficos
    document.querySelectorAll('.chart-section').forEach(section => {
        observer.observe(section);
    });

    // Observa a tabela
    document.querySelectorAll('.table-section').forEach(section => {
        observer.observe(section);
    });
}

// ============================================================
// FILTROS — Interações
// ============================================================

/**
 * Configura os filtros do dashboard para submit automático
 * ao alterar valores.
 */
function initFiltros() {
    const form = document.getElementById('filtros-form');
    if (!form) return;

    const periodoSelect = document.getElementById('filtro-periodo');
    const publicoSelect = document.getElementById('filtro-publico');
    const dataInicio = document.getElementById('filtro-data-inicio');
    const dataFim = document.getElementById('filtro-data-fim');
    const customRange = document.getElementById('custom-range');

    // Submit automático ao mudar filtros
    if (periodoSelect) {
        periodoSelect.addEventListener('change', function () {
            // Mostrar/esconder campos de data customizada
            if (this.value === 'custom') {
                if (customRange) customRange.style.display = 'flex';
            } else {
                if (customRange) customRange.style.display = 'none';
                form.submit();
            }
        });
    }

    if (publicoSelect) {
        publicoSelect.addEventListener('change', function () {
            form.submit();
        });
    }

    // Para o range customizado, submit ao mudar ambas as datas
    if (dataInicio) {
        dataInicio.addEventListener('change', function () {
            if (dataFim && dataFim.value) form.submit();
        });
    }
    if (dataFim) {
        dataFim.addEventListener('change', function () {
            if (dataInicio && dataInicio.value) form.submit();
        });
    }

    // Mostrar o range customizado se já estiver selecionado (após reload)
    if (periodoSelect && periodoSelect.value === 'custom') {
        if (customRange) customRange.style.display = 'flex';
    }
}

// ============================================================
// TABELA ORDENÁVEL
// ============================================================

/**
 * Configura ordenação por clique nos cabeçalhos da tabela.
 */
function initTabelaOrdenavel() {
    const tabela = document.getElementById('tabela-campanhas');
    if (!tabela) return;

    const headers = tabela.querySelectorAll('th[data-sort]');
    let sortDirection = {}; // Rastreia direção por coluna

    headers.forEach(header => {
        header.style.cursor = 'pointer';
        header.title = 'Clique para ordenar';

        header.addEventListener('click', function () {
            const sortKey = this.dataset.sort;
            const colIndex = this.cellIndex;
            const tbody = tabela.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));

            // Alterna direção
            sortDirection[sortKey] = !sortDirection[sortKey];
            const ascending = sortDirection[sortKey];

            // Remove indicadores de todas as colunas
            headers.forEach(h => {
                h.classList.remove('sort-asc', 'sort-desc');
            });

            // Adiciona indicador na coluna atual
            this.classList.add(ascending ? 'sort-asc' : 'sort-desc');

            // Ordena as linhas
            rows.sort((a, b) => {
                let valA = a.cells[colIndex].dataset.value || a.cells[colIndex].textContent.trim();
                let valB = b.cells[colIndex].dataset.value || b.cells[colIndex].textContent.trim();

                // Tenta converter para número
                const numA = parseFloat(valA.replace(/[^\d,.-]/g, '').replace(',', '.'));
                const numB = parseFloat(valB.replace(/[^\d,.-]/g, '').replace(',', '.'));

                if (!isNaN(numA) && !isNaN(numB)) {
                    return ascending ? numA - numB : numB - numA;
                }

                // Ordenação alfabética
                return ascending
                    ? valA.localeCompare(valB, 'pt-BR')
                    : valB.localeCompare(valA, 'pt-BR');
            });

            // Re-insere as linhas ordenadas
            rows.forEach(row => tbody.appendChild(row));
        });
    });
}

// ============================================================
// CONFIRMAÇÃO DE EXCLUSÃO
// ============================================================

/**
 * Adiciona confirmação antes de excluir uma campanha.
 */
function initConfirmacaoExclusao() {
    document.querySelectorAll('.btn-excluir').forEach(btn => {
        btn.addEventListener('click', function (e) {
            const nomeCampanha = this.dataset.nome || 'esta campanha';
            if (!confirm(`Tem certeza que deseja excluir "${nomeCampanha}"?\n\nEsta ação não pode ser desfeita.`)) {
                e.preventDefault();
            }
        });
    });
}

// ============================================================
// VALIDAÇÃO DO FORMULÁRIO
// ============================================================

/**
 * Validação adicional no formulário de campanha.
 */
function initValidacaoFormulario() {
    const form = document.getElementById('form-campanha');
    if (!form) return;

    form.addEventListener('submit', function (e) {
        const dataInicio = document.getElementById('data_inicio');
        const dataFim = document.getElementById('data_fim');

        if (dataInicio && dataFim) {
            if (dataFim.value < dataInicio.value) {
                e.preventDefault();
                alert('A data de fim deve ser igual ou posterior à data de início.');
                dataFim.focus();
                return false;
            }
        }

        // Validar valores numéricos positivos
        const camposNumericos = ['valor_gasto', 'visualizacoes', 'conversas_iniciadas', 'entregas'];
        for (const campo of camposNumericos) {
            const el = document.getElementById(campo);
            if (el && parseFloat(el.value) < 0) {
                e.preventDefault();
                alert(`O campo "${el.previousElementSibling?.textContent || campo}" não pode ser negativo.`);
                el.focus();
                return false;
            }
        }
    });
}

// ============================================================
// FLASH MESSAGES — Auto-dismiss
// ============================================================

/**
 * Remove flash messages após alguns segundos.
 */
function initFlashMessages() {
    const messages = document.querySelectorAll('.flash-message');
    messages.forEach(msg => {
        // Adiciona classe de animação de entrada
        msg.classList.add('flash-show');

        // Remove após 5 segundos
        setTimeout(() => {
            msg.classList.add('flash-hide');
            setTimeout(() => msg.remove(), 500);
        }, 5000);

        // Permite fechar manualmente
        const closeBtn = msg.querySelector('.flash-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                msg.classList.add('flash-hide');
                setTimeout(() => msg.remove(), 500);
            });
        }
    });
}

// ============================================================
// MODAL NOVA CAMPANHA — Controle
// ============================================================
function initModal() {
    const modal = document.getElementById('modal-nova-campanha');
    const btnAbrir = document.getElementById('btn-nova-campanha-modal');
    const btnFechar = document.getElementById('btn-fechar-modal');
    const btnCancelar = document.getElementById('btn-cancelar-modal');
    const formModal = document.getElementById('form-campanha-modal');
    const datalist = document.getElementById('modal-publicos-lista');

    if (!modal || !btnAbrir) return;

    // Abrir Modal
    btnAbrir.addEventListener('click', () => {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';

        // Popula a datalist de forma assíncrona
        if (datalist && datalist.children.length === 0) {
            fetch('/api/publicos')
                .then(res => res.json())
                .then(publicos => {
                    datalist.innerHTML = '';
                    publicos.forEach(p => {
                        const opt = document.createElement('option');
                        opt.value = p;
                        datalist.appendChild(opt);
                    });
                })
                .catch(err => console.error('Erro ao buscar públicos:', err));
        }
    });

    // Fechar Modal
    const fecharModal = () => {
        modal.classList.remove('show');
        document.body.style.overflow = '';
        if (formModal) formModal.reset();
    };

    if (btnFechar) btnFechar.addEventListener('click', fecharModal);
    if (btnCancelar) btnCancelar.addEventListener('click', fecharModal);

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            fecharModal();
        }
    });

    // Validação no formulário do modal
    if (formModal) {
        formModal.addEventListener('submit', function (e) {
            const dataInicio = document.getElementById('modal_data_inicio');
            const dataFim = document.getElementById('modal_data_fim');

            if (dataInicio && dataFim) {
                if (dataFim.value < dataInicio.value) {
                    e.preventDefault();
                    alert('A data de fim deve ser igual ou posterior à data de início.');
                    dataFim.focus();
                    return false;
                }
            }

            // Validar valores numéricos positivos
            const camposNumericos = [
                { id: 'modal_valor_gasto', label: 'Valor Gasto' },
                { id: 'modal_visualizacoes', label: 'Views' },
                { id: 'modal_conversas_iniciadas', label: 'Conv. Inic.' },
                { id: 'modal_entregas', label: 'Entregas' }
            ];
            for (const campo of camposNumericos) {
                const el = document.getElementById(campo.id);
                if (el && parseFloat(el.value) < 0) {
                    e.preventDefault();
                    alert(`O campo "${campo.label}" não pode ser negativo.`);
                    el.focus();
                    return false;
                }
            }
        });
    }
}

// ============================================================
// INICIALIZAÇÃO
// ============================================================

document.addEventListener('DOMContentLoaded', function () {
    initScrollAnimations();
    initFiltros();
    initTabelaOrdenavel();
    initConfirmacaoExclusao();
    initValidacaoFormulario();
    initFlashMessages();
    initModal();

    if (window.lucide) {
        lucide.createIcons();
    }
});
