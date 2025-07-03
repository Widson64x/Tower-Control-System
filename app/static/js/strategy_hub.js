document.addEventListener('DOMContentLoaded', function () {
    console.log("Hub de People Analytics: Carregado e corrigido.");

    if (!window.GridStack || !window.ApexCharts) {
        console.error("Erro Crítico: Bibliotecas essenciais (GridStack, ApexCharts) não carregadas.");
        return;
    }

    const grid = GridStack.init({
        float: true, cellHeight: 80, margin: 20,
        disableResize: true, disableDrag: true,
    });

    const chartColors = ['#1976d2', '#ffab40', '#4caf50', '#f44336', '#9c27b0', '#795548'];
    const commonChartOptions = {
        chart: { fontFamily: 'Inter, sans-serif', background: 'transparent', toolbar: { show: false } },
        dataLabels: { enabled: false }, stroke: { curve: 'smooth', width: 3 },
        markers: { size: 5 }, tooltip: { theme: 'dark' },
        legend: { labels: { colors: '#888' } }
    };

    const widgetFactory = {
        vitalMetrics: (grid, pos, apiUrl) => {
            fetch(apiUrl).then(res => res.json()).then(data => {
                let cards = '';
                Object.values(data).forEach(item => {
                    let value = (typeof item.value === 'number' && item.label.includes('Mensal')) 
                        ? `R$ ${(item.value / 1000).toFixed(0)}k` 
                        : item.value;
                    cards += `<div class="col"><div class="kpi-card-inner">
                                <p class="kpi-value mb-1">${value}</p>
                                <p class="kpi-label text-uppercase mb-0">${item.label}</p>
                              </div></div>`;
                });
                const content = `<div class="widget-header">Indicadores-Chave</div><div class="widget-body row">${cards}</div>`;
                grid.addWidget({ ...pos, content, id: 'kpi-widget' });
            });
        },
        headcountFlow: (grid, pos, apiUrl) => {
            const chartId = "headcount-flow-chart";
            const content = `<div class="widget-header">Fluxo de Pessoal (Últimos 6 Meses)</div><div class="widget-body"><div id="${chartId}"></div></div>`;
            grid.addWidget({ ...pos, content, id: 'headcount-flow-widget' });
            fetch(apiUrl).then(res => res.json()).then(data => {
                new ApexCharts(document.querySelector(`#${chartId}`), {
                    ...commonChartOptions, chart: { type: 'bar', stacked: false, ...commonChartOptions.chart }, colors: [chartColors[2], chartColors[3]],
                    series: data.series, xaxis: { categories: data.labels }, plotOptions: { bar: { horizontal: false, columnWidth: '60%' } },
                    legend: { position: 'top', horizontalAlign: 'right' }
                }).render();
            });
        },
        performanceDistribution: (grid, pos, apiUrl) => {
            const chartId = "performance-chart";
            const content = `<div class="widget-header">Distribuição de Performance</div><div class="widget-body"><div id="${chartId}"></div></div>`;
            grid.addWidget({ ...pos, content, id: 'performance-widget' });
            fetch(apiUrl).then(res => res.json()).then(data => {
                new ApexCharts(document.querySelector(`#${chartId}`), {
                    ...commonChartOptions, chart: { type: 'donut', ...commonChartOptions.chart }, colors: chartColors,
                    series: data.series, labels: data.labels, legend: { position: 'bottom' },
                }).render();
            });
        },
        performanceByTeam: (grid, pos, apiUrl) => {
            const chartId = "team-performance-chart";
            const content = `<div class="widget-header">Performance Média por Equipe</div><div class="widget-body"><div id="${chartId}"></div></div>`;
            grid.addWidget({ ...pos, content, id: 'team-performance-widget' });
            fetch(apiUrl).then(res => res.json()).then(data => {
                new ApexCharts(document.querySelector(`#${chartId}`), {
                    ...commonChartOptions, chart: { type: 'bar', ...commonChartOptions.chart }, colors: [chartColors[0]],
                    series: data.series, xaxis: { categories: data.labels }, plotOptions: { bar: { horizontal: true, barHeight: '60%', distributed: true } },
                    legend: { show: false }, grid: { xaxis: { lines: { show: true } } }
                }).render();
            });
        },
        employeeJourney: (grid, pos, apiUrl) => {
            const chartId = "sankey-chart";
            const content = `<div class="widget-header">Jornada do Colaborador (Fluxo Anual)</div><div class="widget-body"><div id="${chartId}"></div></div>`;
            grid.addWidget({ ...pos, content, id: 'sankey-widget' });
            fetch(apiUrl).then(res => res.json()).then(data => {
                new ApexCharts(document.querySelector(`#${chartId}`), {
                    ...commonChartOptions, chart: { type: 'sankey', ...commonChartOptions.chart },
                    series: [{ name: 'Fluxo', data: data }], title: { text: '' }
                }).render();
            });
        }
    };

    function loadHubLayout() {
        grid.batchUpdate();
        widgetFactory.vitalMetrics(grid, {x:0, y:0, w:12, h:2}, '/kpis/api/vital-metrics');
        widgetFactory.headcountFlow(grid, {x:0, y:2, w:8, h:4}, '/kpis/api/headcount-flow');
        widgetFactory.performanceDistribution(grid, {x:8, y:2, w:4, h:4}, '/kpis/api/performance-distribution');
        widgetFactory.performanceByTeam(grid, {x:0, y:6, w:12, h:5}, '/kpis/api/performance-by-team');
        widgetFactory.employeeJourney(grid, {x:0, y:11, w:12, h:5}, '/kpis/api/employee-journey-sankey');
        grid.commit();
    }
    
    loadHubLayout();
});