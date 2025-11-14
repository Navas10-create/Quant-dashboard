async function loadSignals() {
  const tableBody = document.querySelector('#signalsBody');
  try {
    const res = await fetch('/api/signals');
    const json = await res.json();

    if (json.status !== 'success') {
      tableBody.innerHTML = `<tr><td colspan="5" style="color:#ff5252;">${json.message}</td></tr>`;
      return;
    }

    const data = json.data.sort((a, b) => new Date(b.time) - new Date(a.time)); // newest first

    if (!data.length) {
      tableBody.innerHTML = `<tr><td colspan="5">No signals yet.</td></tr>`;
      return;
    }

    tableBody.innerHTML = data.map(sig => {
      const time = new Date(sig.time).toLocaleString();
      const color = sig.side === 'BUY' ? '#00e676' : sig.side === 'SELL' ? '#ff5252' : '#ccc';
      return `
        <tr style="color:${color}; transition: background 0.3s;" 
            onmouseover="this.style.background='#222';" 
            onmouseout="this.style.background='';">
          <td>${time}</td>
          <td>${sig.symbol || ''}</td>
          <td>${sig.side || ''}</td>
          <td>${sig.price ? sig.price.toFixed(2) : ''}</td>
          <td>${sig.note || ''}</td>
        </tr>`;
    }).join('');
  } catch (err) {
    console.error(err);
    tableBody.innerHTML = `<tr><td colspan="5" style="color:#ff5252;">Error loading signals</td></tr>`;
  }
}

document.getElementById('refreshSignals')?.addEventListener('click', loadSignals);
window.addEventListener('load', () => {
  loadSignals();
  setInterval(loadSignals, 8000);
});
