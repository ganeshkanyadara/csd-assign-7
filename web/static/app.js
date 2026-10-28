document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const statusBadge = document.getElementById('api-status-badge');
  const searchForm = document.getElementById('search-form');
  const latInput = document.getElementById('lat');
  const longInput = document.getElementById('long');
  const catInput = document.getElementById('cat');
  const radSlider = document.getElementById('rad-slider');
  const radHidden = document.getElementById('rad');
  const radVal = document.getElementById('rad-val');
  const linkMode = document.getElementById('link-mode');
  const linkFile = document.getElementById('link-file');
  const fileUploadGroup = document.getElementById('file-upload-group');
  const httpMethod = document.getElementById('http-method');
  const btnSearch = document.getElementById('btn-search');
  const searchSpinner = document.getElementById('search-spinner');
  const statLatency = document.getElementById('stat-latency');
  const statStatus = document.getElementById('stat-status');
  const statCount = document.getElementById('stat-count');
  const jsonOutput = document.getElementById('json-output');
  const resultsBody = document.getElementById('results-body');
  const btnCopy = document.getElementById('btn-copy');
  const canvas = document.getElementById('gridCanvas');
  const ctx = canvas.getContext('2d');

  // Slider sync
  radSlider.addEventListener('input', (e) => {
    const val = parseFloat(e.target.value).toFixed(2);
    radVal.textContent = val;
    radHidden.value = val;
    drawGrid(parseFloat(latInput.value), parseFloat(longInput.value), parseFloat(val), currentResults);
  });

  // Link mode toggle
  linkMode.addEventListener('change', (e) => {
    fileUploadGroup.style.display = e.target.value === 'file' ? 'flex' : 'none';
  });

  // Presets
  document.querySelectorAll('.btn-preset').forEach(btn => {
    btn.addEventListener('click', () => {
      latInput.value = btn.dataset.lat;
      longInput.value = btn.dataset.long;
      catInput.value = btn.dataset.cat;
      radSlider.value = btn.dataset.rad;
      radVal.textContent = parseFloat(btn.dataset.rad).toFixed(2);
      radHidden.value = btn.dataset.rad;
      drawGrid(parseFloat(latInput.value), parseFloat(longInput.value), parseFloat(radHidden.value), currentResults);
    });
  });

  // Copy JSON
  btnCopy.addEventListener('click', () => {
    navigator.clipboard.writeText(jsonOutput.textContent);
    btnCopy.textContent = 'Copied!';
    setTimeout(() => { btnCopy.textContent = 'Copy JSON'; }, 1500);
  });

  let currentResults = [];

  // Health check polling
  async function checkHealth() {
    try {
      const res = await fetch('/health');
      if (res.ok) {
        const data = await res.json();
        statusBadge.textContent = `Online (${data.total_locations} locs)`;
        statusBadge.className = 'badge healthy';
      } else {
        throw new Error('Health check non-200');
      }
    } catch (err) {
      statusBadge.textContent = 'Offline / Connecting';
      statusBadge.className = 'badge error';
    }
  }
  checkHealth();
  setInterval(checkHealth, 15000);

  // Canvas drawing
  function drawGrid(queryLat, queryLon, radius, results = []) {
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    // Draw background grid lines (10x10 major lines for the 100x100 grid)
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 10; i++) {
      const pos = (i / 10) * w;
      ctx.beginPath();
      ctx.moveTo(pos, 0);
      ctx.lineTo(pos, h);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(0, pos);
      ctx.lineTo(w, pos);
      ctx.stroke();
    }

    if (isNaN(queryLat) || isNaN(queryLon)) return;

    // Convert normalized (0.0 - 1.0) coordinates to canvas pixel space
    // Latitude -> y (inverted: 0.0 bottom, 1.0 top)
    // Longitude -> x (0.0 left, 1.0 right)
    const qX = queryLon * w;
    const qY = (1.0 - queryLat) * h;
    const radPx = (radius || 0.2) * w;

    // 1. Draw circular search radius
    ctx.beginPath();
    ctx.arc(qX, qY, radPx, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(59, 130, 246, 0.12)';
    ctx.fill();
    ctx.strokeStyle = 'rgba(59, 130, 246, 0.5)';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.stroke();
    ctx.setLineDash([]);

    // 2. Draw results
    if (results && results.length > 0) {
      results.forEach((lid, idx) => {
        // Location ID to 100x100 grid coordinate: ID = r * 100 + c + 1
        // r in [0..99], c in [0..99]
        // lat = r / 99.0, lon = c / 99.0
        const id0 = lid - 1;
        const r = Math.floor(id0 / 100);
        const c = id0 % 100;
        const rLat = r / 99.0;
        const rLon = c / 99.0;
        const ptX = rLon * w;
        const ptY = (1.0 - rLat) * h;

        // Line to center
        ctx.beginPath();
        ctx.moveTo(qX, qY);
        ctx.lineTo(ptX, ptY);
        ctx.strokeStyle = 'rgba(16, 185, 129, 0.25)';
        ctx.lineWidth = 1;
        ctx.stroke();

        // Location marker
        ctx.beginPath();
        ctx.arc(ptX, ptY, 5, 0, Math.PI * 2);
        ctx.fillStyle = '#10b981';
        ctx.fill();
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Rank label
        ctx.fillStyle = '#f8fafc';
        ctx.font = 'bold 10px monospace';
        ctx.fillText(`#${idx + 1}`, ptX + 8, ptY + 3);
      });
    }

    // 3. Draw query center point (Red)
    ctx.beginPath();
    ctx.arc(qX, qY, 7, 0, Math.PI * 2);
    ctx.fillStyle = '#ef4444';
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.stroke();
  }

  // Initial draw
  drawGrid(0.505051, 0.505051, 0.20, []);

  // Form submit
  searchForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const lat = parseFloat(latInput.value);
    const lon = parseFloat(longInput.value);
    const cat = catInput.value;
    const rad = parseFloat(radHidden.value);
    const method = httpMethod.value;

    btnSearch.disabled = true;
    searchSpinner.style.display = 'inline-block';
    statLatency.textContent = '...';
    statStatus.textContent = '...';

    const tStart = performance.now();

    try {
      let res;
      if (method === 'GET') {
        const params = new URLSearchParams({
          lat: lat,
          long: lon,
          cat: cat,
          rad: rad,
          link: 'link.txt'
        });
        res = await fetch(`/search/?${params.toString()}`);
      } else if (method === 'POST-JSON') {
        const payload = {
          lat: lat,
          long: lon,
          cat: cat,
          rad: rad,
          link: 'link.txt'
        };
        res = await fetch('/search/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      } else if (method === 'POST-FORM') {
        const formData = new FormData();
        formData.append('lat', lat);
        formData.append('long', lon);
        formData.append('cat', cat);
        formData.append('rad', rad);
        if (linkMode.value === 'file' && linkFile.files.length > 0) {
          formData.append('link', linkFile.files[0]);
        } else {
          formData.append('link', 'link.txt');
        }
        res = await fetch('/search/', {
          method: 'POST',
          body: formData
        });
      }

      const tDuration = Math.round(performance.now() - tStart);
      statLatency.textContent = `${tDuration} ms`;
      statStatus.textContent = `${res.status} ${res.statusText}`;

      if (res.ok) {
        const data = await res.json();
        currentResults = Array.isArray(data) ? data : (data.recommended_locations || []);
        statCount.textContent = currentResults.length;
        jsonOutput.textContent = JSON.stringify(currentResults, null, 2);

        // Populate Table
        resultsBody.innerHTML = '';
        currentResults.forEach((lid, idx) => {
          const id0 = lid - 1;
          const r = Math.floor(id0 / 100);
          const c = id0 % 100;
          const rLat = (r / 99.0).toFixed(4);
          const rLon = (c / 99.0).toFixed(4);

          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td>#${idx + 1}</td>
            <td style="color:#60a5fa; font-weight:600;">${lid}</td>
            <td><span class="badge" style="text-transform:capitalize;">${cat}</span></td>
            <td>(${rLon}, ${rLat})</td>
            <td style="color:#34d399;">Valid</td>
          `;
          resultsBody.appendChild(tr);
        });

        // Update canvas
        drawGrid(lat, lon, rad, currentResults);
      } else {
        const errText = await res.text();
        jsonOutput.textContent = `Error ${res.status}: ${errText}`;
        currentResults = [];
        statCount.textContent = '0';
        drawGrid(lat, lon, rad, []);
      }
    } catch (err) {
      const tDuration = Math.round(performance.now() - tStart);
      statLatency.textContent = `${tDuration} ms`;
      statStatus.textContent = 'Network Error';
      jsonOutput.textContent = `Fetch error: ${err.message}`;
    } finally {
      btnSearch.disabled = false;
      searchSpinner.style.display = 'none';
    }
  });
});
