document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-password-target]').forEach(button => {
    button.addEventListener('click', () => {
      const input = document.getElementById(button.dataset.passwordTarget);
      const reveal = input.type === 'password';
      input.type = reveal ? 'text' : 'password';
      button.textContent = reveal ? 'Yashirish' : 'Ko‘rsatish';
      button.setAttribute('aria-pressed', String(reveal));
    });
  });
  const filter = document.getElementById('edu-module-search');
  if (filter) filter.addEventListener('input', () => {
    const term = filter.value.toLocaleLowerCase().trim();
    document.querySelectorAll('[data-module-name]').forEach(row => {
      row.hidden = !row.dataset.moduleName.toLocaleLowerCase().includes(term);
    });
  });
  const chart = document.getElementById('edu-chart-data');
  if (!chart) return;
  const data = JSON.parse(chart.textContent);
  const plot = document.getElementById('edu-chart');
  const summary = document.getElementById('edu-chart-summary');
  const tabs = document.querySelectorAll('[data-chart-metric]');
  const money = new Intl.NumberFormat('uz-UZ', { maximumFractionDigits: 0 });
  const render = metric => {
    const max = Math.max(...data.map(d => d[metric]), 1);
    plot.replaceChildren();
    const total = data.reduce((n, d) => n + d[metric], 0);
    summary.textContent = money.format(total) + (metric === 'revenue' ? ' so‘m' : ' ta yangi foydalanuvchi');
    data.forEach(item => {
      const bar = document.createElement('button');
      bar.type = 'button';
      bar.className = 'edu-chart-bar';
      bar.style.setProperty('--bar-height', `${Math.max(item[metric] / max * 100, 1.5)}%`);
      bar.setAttribute('aria-label', `${item.label}: ${money.format(item[metric])}${metric === 'revenue' ? ' so‘m' : ' ta'}`);
      bar.title = bar.getAttribute('aria-label');
      bar.addEventListener('focus', () => { document.getElementById('edu-chart-detail').textContent = bar.title; });
      bar.addEventListener('pointerenter', () => { document.getElementById('edu-chart-detail').textContent = bar.title; });
      plot.appendChild(bar);
    });
    document.getElementById('edu-chart-detail').textContent = total ? 'Kunlik qiymatni ko‘rish uchun ustunni tanlang.' : 'Tanlangan davrda ma’lumot yo‘q.';
    tabs.forEach(tab => tab.setAttribute('aria-pressed', String(tab.dataset.chartMetric === metric)));
  };
  tabs.forEach(tab => tab.addEventListener('click', () => render(tab.dataset.chartMetric)));
  if (tabs.length) render(tabs[0].dataset.chartMetric);
});
