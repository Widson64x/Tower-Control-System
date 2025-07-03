document.addEventListener('DOMContentLoaded', function () {
    console.log("Strategy Hub: Ativado. Prepare-se para uma experiência sensacional.");

    if (!window.GridStack || !window.ApexCharts || !window.vis) {
        console.error("Erro Crítico: Bibliotecas essenciais não carregadas (GridStack, ApexCharts, Vis.js).");
        return;
    }

    const grid = GridStack.init({
        float: true,
        cellHeight: 80,
        margin: 20,
        disableResize: true, // Layout curado, sem redimensionamento pelo usuário
        disableDrag: true,   // Layout fixo
    });

    const commonChartOptions = {
        chart: { fontFamily: 'Inter, sans-serif', background: 'transparent', toolbar: { show: false } },
        dataLabels: { enabled: false },
    };

    const widgetFactory = {
        kpiCard: (grid, {x, y, w=3, h=2}, apiUrl) => {
            fetch(apiUrl).then(res => res.json()).then(data => {
                let cards = '';
                Object.keys(data).forEach(key => {
                    let value = data[key].value;
                    if (key === 'total_payroll') {
                        value = (value / 1000).toFixed(1) + 'k';
                    }
                    cards += `<div class="col-6 mb-3">
                                <p class="kpi-value mb-1">${value}</p>
                                <p class="kpi-label text-uppercase">${data[key].label}</p>
                              </div>`;
                });
                const content = `<div class="widget-header">Métricas Vitais</div><div class="widget-body row">${cards}</div>`;
                grid.addWidget({x, y, w, h, content: content});
            });
        },
        sankey: (grid, {x, y, w, h}, apiUrl) => {
            const content = `<div class="widget-header">Jornada do Colaborador (Fluxo de Promoções)</div><div class="widget-body" id="sankey-chart"></div>`;
            grid.addWidget({x, y, w, h, content: content});
            fetch(apiUrl).then(res => res.json()).then(data => {
                const options = {
                    ...commonChartOptions,
                    chart: { type: 'sankey', ...commonChartOptions.chart },
                    series: [{ data: data }],
                    title: { text: '' },
                };
                new ApexCharts(document.querySelector("#sankey-chart"), options).render();
            });
        },
        polar: (grid, {x, y, w, h}, apiUrl) => {
            const content = `<div class="widget-header">Distribuição de Performance</div><div class="widget-body" id="polar-chart"></div>`;
            grid.addWidget({x, y, w, h, content: content});
            fetch(apiUrl).then(res => res.json()).then(data => {
                const options = {
                    ...commonChartOptions,
                    chart: { type: 'polarArea', ...commonChartOptions.chart },
                    stroke: { colors: ['#fff'] }, fill: { opacity: 0.8 },
                    series: data.series, labels: data.labels,
                    legend: { position: 'bottom' },
                };
                new ApexCharts(document.querySelector("#polar-chart"), options).render();
            });
        },
        network: (grid, {x, y, w, h}, apiUrl) => {
            const containerId = "network-graph";
            const content = `<div class="widget-header">Rede de Colaboração (Feedbacks)</div><div class="widget-body"><div id="${containerId}" style="width:100%;height:100%;"></div></div>`;
            grid.addWidget({x, y, w, h, content: content});
            fetch(apiUrl).then(res => res.json()).then(data => {
                const container = document.getElementById(containerId);
                const networkData = { nodes: new vis.DataSet(data.nodes), edges: new vis.DataSet(data.edges) };
                const options = {
                    nodes: { shape: 'dot', size: 16, font: { size: 14 } },
                    edges: { width: 2 },
                    physics: { barnesHut: { gravitationalConstant: -3000 } },
                    interaction: { hover: true },
                    groups: { // Colore os nós por time
                        'Tecnologia': { color: { background: '#0077C8', border: '#004282' } },
                        'Marketing': { color: { background: '#00BF63', border: '#008c4a' } },
                        // Adicione outras equipes
                    }
                };
                new vis.Network(container, networkData, options);
            });
        }
    };

    function loadHubLayout() {
        grid.batchUpdate();
        
        // Linha 1: KPIs principais e o gráfico Polar
        widgetFactory.kpiCard(grid, {x:0, y:0}, '/kpis/api/kpi-summary');
        widgetFactory.polar(grid, {x:3, y:0, w:4, h:4}, '/kpis/api/performance-distribution-polar');
        widgetFactory.network(grid, {x:7, y:0, w:5, h:4}, '/kpis/api/feedback-network');
        
        // Linha 2: O gráfico "Uau" de Sankey ocupando a largura toda
        widgetFactory.sankey(grid, {x:0, y:4, w:12, h:4}, '/kpis/api/employee-journey-sankey');
        
        grid.commit();
    }
    
    loadHubLayout();
});