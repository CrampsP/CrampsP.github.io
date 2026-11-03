'use strict';
const $ = (id) => document.getElementById(id);
const state = { snapshot: null, mode: 'live', view: 'overview', auto: true, busy: false, error: null };
const titles = {
  overview: ['A clearer view of your network.', 'Know what’s listening, where traffic goes, and what deserves a closer look.'],
  findings: ['Security findings', 'Explainable review priorities. Inspect the evidence before deciding how to harden.'],
  listeners: ['Listening ports', 'TCP listeners and UDP bindings on this Windows computer. Remote reachability remains unverified.'],
  connections: ['Live connections', 'Windows TCP socket snapshots with processes, endpoints and inferred traffic direction.'],
  devices: ['Devices & services', 'Your host, observed Windows services, and devices present in the passive neighbor cache.'],
  methodology: ['Evidence & monitoring limits', 'Understand what is observed, what is inferred, and where human judgment matters.']
};
const escapeHtml = (value) => String(value ?? '—').replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const fmtTime = (value) => value ? new Date(value).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'}) : '—';
const endpoint = (address, port) => `${String(address).includes(':')?'['+escapeHtml(address)+']':escapeHtml(address)}:${port}`;
const badge = (priority) => `<span class="mini-tag ${{high:'red',medium:'amber',low:'blue',info:'mint'}[priority] || 'blue'}">${escapeHtml(priority.toUpperCase())}</span>`;
const table = (headers, rows) => `<div class="table-wrap"><table><thead><tr>${headers.map(h=>`<th scope="col">${h}</th>`).join('')}</tr></thead><tbody>${rows.length ? rows.join('') : `<tr><td class="table-empty" colspan="${headers.length}">No rows match. Reset filters or wait for another snapshot.</td></tr>`}</tbody></table></div>`;
const cell = (value) => `<td>${value}</td>`;

function setView() {
  const name = location.hash.slice(1);
  state.view = Object.hasOwn(titles, name) ? name : 'overview';
  $('page-title').textContent = titles[state.view][0];
  $('page-subtitle').textContent = titles[state.view][1];
  $('breadcrumb').textContent = state.view === 'overview' ? 'Overview' : titles[state.view][0];
  document.querySelectorAll('.nav-link').forEach(link => {
    const active = link.dataset.view === state.view;
    link.classList.toggle('active', active);
    if (active) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current');
  });
  $('overview').hidden = state.view !== 'overview';
  $('methodology').hidden = state.view !== 'methodology';
  $('data-view').hidden = ['overview','methodology'].includes(state.view);
  const device = state.view === 'devices';
  $('priority-filter').disabled = device;
  $('protocol-filter').disabled = device;
  $('scope-filter').disabled = device || state.view === 'findings';
  renderView();
}

function filters() {
  return {search:$('search').value.trim().toLowerCase(), priority:$('priority-filter').value,
    protocol:$('protocol-filter').value, scope:$('scope-filter').value};
}

function filterRows(rows, kind) {
  const f = filters();
  return rows.filter(row => {
    if (f.search && !JSON.stringify(row).toLowerCase().includes(f.search)) return false;
    if (kind === 'devices') return true;
    if (f.priority !== 'all' && row.priority !== f.priority) return false;
    if (f.protocol !== 'all' && row.protocol !== f.protocol && !(kind==='findings' && row.evidence.startsWith(f.protocol+' '))) return false;
    if (kind==='findings') return true;
    const scope = kind==='connections' ? row.remote_scope : row.scope;
    if (f.scope === 'network' && ['loopback','unknown'].includes(scope)) return false;
    if (f.scope === 'loopback' && scope !== 'loopback') return false;
    if (f.scope === 'public' && (kind!=='connections' || scope !== 'public')) return false;
    return true;
  });
}

function findingRow(finding) {
  const color = {high:'red', medium:'amber', low:'blue', info:'mint'}[finding.priority];
  return `<button class="finding-row" data-finding="${escapeHtml(finding.id)}"><span class="finding-symbol ${color}" aria-hidden="true">◇</span><span class="finding-body"><h3>${escapeHtml(finding.title)}</h3><p>${escapeHtml(finding.evidence)}</p><span class="finding-meta">${badge(finding.priority)}<span>${escapeHtml(finding.category)}</span><span>${escapeHtml(finding.confidence)} confidence</span></span></span><span class="finding-arrow" aria-hidden="true">↗</span></button>`;
}

function renderOverview() {
  const s = state.snapshot;
  if (!s) return;
  $('metric-high').textContent = s.summary.high;
  $('metric-listeners').textContent = s.summary.network_listeners;
  $('metric-public').textContent = s.summary.public_connections;
  $('metric-gaps').textContent = s.summary.visibility_gaps;
  $('nav-findings').textContent = s.findings.length;
  $('priority-list').innerHTML = s.findings.length ? s.findings.slice(0,4).map(findingRow).join('') : '<p class="empty">No configured review rules matched this snapshot. This does not establish that the host is secure.</p>';
  $('ring-count').textContent = s.summary.network_listeners;
  $('legend-network').textContent = s.summary.network_listeners;
  $('legend-local').textContent = s.listeners.length - s.summary.network_listeners;
  $('ring-value').setAttribute('stroke-dasharray', `${453*(s.summary.network_listeners/Math.max(s.listeners.length,1))} 453`);
  const firewall = s.firewall_profiles.map(p => `${p.name}: ${p.enabled ? 'on':'OFF'}`).join(' · ') || 'Unavailable';
  const details = [['Source',s.mode==='demo'?'Synthetic demonstration':'Windows terminal collector'],
    ['TCP connections',s.connections.length],['Endpoints',s.listeners.length],
    ['Firewall profiles',firewall],['Collection time',s.collection_duration_ms==null?'Unknown':`${s.collection_duration_ms} ms`]];
  $('collector-details').innerHTML = details.map(([label,value])=>`<div class="collector-line"><span>${escapeHtml(label)}</span><span>${escapeHtml(value)}</span></div>`).join('');
  if (s.errors.length) $('collector-details').innerHTML += `<div class="collector-line"><span>Visibility gaps</span><span>${s.errors.map(escapeHtml).join('<br>')}</span></div>`;
  $('limitations').innerHTML = s.limitations.map(item=>`<li>${escapeHtml(item)}</li>`).join('');
  renderChart(s.history);
}

function renderChart(history) {
  $('history-label').textContent = state.mode==='demo' ? 'Demo · no live history' : `${history.length} samples`;
  if (history.length<2) {
    $('activity-chart').innerHTML = `<p class="empty">${state.mode==='demo'?'Demo mode does not fabricate a live activity history.':'A trend appears after two distinct collector snapshots.'}</p>`;
    $('activity-range').textContent = '—';
    return;
  }
  const max = Math.max(4,...history.map(h=>h.established));
  const points = history.map((row,i)=>[30+i*660/(history.length-1),118-row.established/max*103]);
  const line = points.map(p=>p.join(',')).join(' ');
  $('activity-chart').innerHTML = `<svg viewBox="0 0 700 145" role="img" aria-label="Established TCP connections, ranging from ${Math.min(...history.map(h=>h.established))} to ${Math.max(...history.map(h=>h.established))}"><line class="grid-line" x1="30" x2="690" y1="15" y2="15"/><line class="grid-line" x1="30" x2="690" y1="66" y2="66"/><line class="grid-line" x1="30" x2="690" y1="118" y2="118"/><text class="chart-label" x="0" y="19">${max}</text><text class="chart-label" x="0" y="122">0</text><polygon class="chart-area" points="30,118 ${line} 690,118"/><polyline class="chart-line" points="${line}"/><circle class="chart-point" cx="${points.at(-1)[0]}" cy="${points.at(-1)[1]}" r="3"/></svg>`;
  $('activity-range').textContent = `${fmtTime(history[0].at)} – ${fmtTime(history.at(-1).at)}`;
}

function renderView() {
  const s = state.snapshot;
  if (['overview','methodology'].includes(state.view)) return;
  if (!s) { $('view-content').innerHTML='<div class="panel empty">No snapshot available. Start the Windows collector or explore the labeled demo.</div>'; $('result-count').textContent='No data'; $('view-note').textContent=''; return; }
  const kind = state.view;
  if (kind==='devices') { renderDevices(s); return; }
  const all = s[kind];
  const rows = filterRows(all,kind);
  $('result-count').textContent = `${rows.length} of ${all.length} ${kind==='listeners'?'endpoints':kind}`;
  $('view-note').textContent = kind==='listeners'?'Service hints are inferred from ports; Windows services are observed.':kind==='connections'?'Direction inferred · all TCP states · no payload inspection':'Review priorities, not confirmed vulnerabilities.';
  if (kind==='findings') {
    $('view-content').innerHTML = `<div class="priority-list">${rows.length ? rows.map(findingRow).join('') : '<div class="panel empty">No findings match these filters. No findings is not proof of security.</div>'}</div>`;
  } else if (kind==='listeners') {
    $('view-content').innerHTML = table(['Priority','Protocol / endpoint','Process / PID','Service evidence','Binding / internet'],rows.map(r=>'<tr>'+[
      badge(r.priority),`<code>${escapeHtml(r.protocol)} ${endpoint(r.local_address,r.local_port)}</code><small>${escapeHtml(r.state)}</small>`,
      `${escapeHtml(r.process_name)} <small>PID ${r.pid} · ${escapeHtml(r.process_path || 'Executable path unavailable')}</small>`,
      `${escapeHtml(r.service_hint)}<small>Port hint · not a confirmed product</small><small>Windows services: ${escapeHtml((r.services||[]).join(', ') || 'None mapped')}</small>`,
      `<span class="scope-label">${escapeHtml(r.scope)}</span><small>Internet: Unverified</small>`].map(cell).join('')+'</tr>'));
  } else if (kind==='connections') {
    $('view-content').innerHTML = table(['Priority / state','Process / PID','Local endpoint','Remote endpoint','Direction / first seen'],rows.map(r=>'<tr>'+[
      `${badge(r.priority)}<small class="state-label">${escapeHtml(r.state)}</small>`,`${escapeHtml(r.process_name)}<small>PID ${r.pid} · ${escapeHtml(r.process_path || 'Path unavailable')}</small>`,
      `<code>${endpoint(r.local_address,r.local_port)}</code>`, `<code>${endpoint(r.remote_address,r.remote_port)}</code><small>${escapeHtml(r.remote_scope)} · ${escapeHtml(r.service_hint)} (port hint)</small>`,
      `${escapeHtml(r.direction)}<small>First observed in server session: ${fmtTime(r.first_seen)}</small>`].map(cell).join('')+'</tr>'));
  }
}

function renderDevices(s) {
  const interfaces = filterRows(s.interfaces,'devices');
  const neighbors = filterRows(s.neighbors,'devices');
  const services = [...new Map(s.listeners.flatMap(row=>(row.services||[]).map(service=>[`${service}|${row.pid}`,{service,pid:row.pid,process_name:row.process_name}]))).values()];
  const serviceRows = filterRows(services,'devices');
  $('result-count').textContent = `${interfaces.length} interfaces · ${neighbors.length} cached neighbors · ${serviceRows.length} local Windows service mappings`;
  $('view-note').textContent = 'Passive discovery only. No neighbor ports are scanned.';
  $('view-content').innerHTML = `<div class="panel device-card"><div class="eyebrow">OBSERVED LOCAL HOST</div><h3>${escapeHtml(s.host)}</h3><p>Only this computer’s sockets, process identities and service associations are monitored.</p></div><h2 class="device-section-title">Local interfaces</h2>`+
    table(['Interface','Address / prefix','Family'],interfaces.map(r=>'<tr>'+[escapeHtml(r.alias),`<code>${escapeHtml(r.address)}/${r.prefix_length}</code>`,escapeHtml(r.family)].map(cell).join('')+'</tr>'))+
    '<h2 class="device-section-title">Cached neighbors · entries may be stale, virtual or multicast</h2>'+
    table(['Cached address','Link-layer address','State','Interface'],neighbors.map(r=>'<tr>'+[`<code>${escapeHtml(r.address)}</code>`,`<code>${escapeHtml(r.mac)}</code>`,escapeHtml(r.state),escapeHtml(r.interface)].map(cell).join('')+'</tr>'))+
    '<h2 class="device-section-title">Windows services associated with local endpoints</h2>'+
    table(['Windows service','PID','Process'],serviceRows.map(r=>'<tr>'+[escapeHtml(r.service),r.pid,escapeHtml(r.process_name)].map(cell).join('')+'</tr>'));
}

function openFinding(id) {
  const f = state.snapshot?.findings.find(item=>item.id===id);
  if (!f) return;
  $('dialog-badge').innerHTML = badge(f.priority)+` <span class="small muted">${escapeHtml(f.status)} · ${escapeHtml(f.confidence)} confidence</span>`;
  $('dialog-title').textContent=f.title;
  $('dialog-content').innerHTML=`<div class="detail-label">OBSERVED EVIDENCE</div><div class="evidence-box">${escapeHtml(f.evidence)}</div><div class="detail-label">WHY THIS DESERVES REVIEW</div><p>${escapeHtml(f.rationale)}</p><div class="detail-label">SUGGESTED HUMAN REVIEW & HARDENING</div><ol>${f.remediation.map(step=>`<li>${escapeHtml(step)}</li>`).join('')}</ol>`;
  $('finding-dialog').showModal();
}

function clearData() {
  state.snapshot=null;
  ['metric-high','metric-listeners','metric-public','metric-gaps','ring-count','legend-network','legend-local','nav-findings'].forEach(id=>$(id).textContent='—');
  $('ring-value').setAttribute('stroke-dasharray','0 453');
  $('priority-list').innerHTML='<div class="empty">No current snapshot available.</div>';
  $('collector-details').innerHTML='';
  $('activity-chart').innerHTML='<div class="empty">No current history available.</div>';
  $('history-label').textContent='Awaiting samples';
  $('activity-range').textContent='—';
  $('host-name').textContent='Windows host';
  $('last-updated').textContent='No current snapshot';
  $('export').disabled=true;
}

async function refresh() {
  if (state.busy) return;
  state.busy=true;
  $('refresh').disabled=true;
  try {
    const response=await fetch(`/api/snapshot?mode=${state.mode}`,{cache:'no-store',signal:AbortSignal.timeout(8000)});
    const data=await response.json();
    if (!response.ok) throw new Error(data.error || `Server returned ${response.status}`);
    state.snapshot=data;
    state.error=null;
    $('waiting-panel').hidden=true;
    $('notice').hidden=!data.stale;
    $('notice').textContent=data.stale?`STALE SNAPSHOT · Collected ${Math.round(data.age_seconds)} seconds ago. Restart or check the Windows collector; this is not current telemetry.`:'';
    $('status-text').textContent=data.mode==='demo'?'Demonstration mode':data.stale?'Collector stale':'Windows snapshot connected';
    $('status-dot').classList.toggle('waiting',data.stale || data.mode==='demo');
    $('host-name').textContent=data.host;
    $('last-updated').textContent=`Snapshot ${fmtTime(data.collected_at)} · ${Math.round(data.age_seconds)}s old`;
    $('export').disabled=false;
    updateFreshness();
    renderOverview();
    renderView();
  } catch (error) {
    clearData();
    state.error=error.message;
    $('notice').hidden=false;
    $('notice').textContent=error.message;
    $('waiting-panel').hidden=state.mode!=='live';
    $('status-text').textContent='Collector unavailable';
    $('status-dot').classList.add('waiting');
    renderView();
  } finally {
    state.busy=false;
    $('refresh').disabled=false;
  }
}

function updateFreshness() {
  const s=state.snapshot;
  if (!s) return;
  const age=Math.max(0,Math.round((Date.now()-Date.parse(s.collected_at))/1000));
  const stale=state.mode==='live' && age>s.stale_after_seconds;
  $('last-updated').textContent=`Snapshot ${fmtTime(s.collected_at)} · ${age}s old`;
  $('status-text').textContent=state.mode==='demo'?'Demonstration mode':stale?'Collector stale':!state.auto?'Snapshot refresh paused':'Windows snapshot connected';
  $('status-dot').classList.toggle('waiting',stale || state.mode==='demo' || !state.auto);
  $('notice').hidden=!stale;
  $('notice').textContent=stale?`STALE SNAPSHOT · Collected ${age} seconds ago. Check the Windows collector or resume refresh; this is not current telemetry.`:'';
}

document.addEventListener('click',event=>{
  const finding=event.target.closest('[data-finding]');
  if (finding) openFinding(finding.dataset.finding);
});
$('dialog-close').addEventListener('click',()=>$('finding-dialog').close());
$('refresh').addEventListener('click',refresh);
$('auto-refresh').addEventListener('click',()=>{
  state.auto=!state.auto;
  $('auto-refresh').textContent=`Auto refresh: ${state.auto?'on':'off'}`;
  $('auto-refresh').setAttribute('aria-pressed',String(state.auto));
  updateFreshness();
  if (state.auto) refresh();
});
$('demo-toggle').addEventListener('click',async()=>{
  if (state.busy) return;
  if ($('finding-dialog').open) $('finding-dialog').close();
  state.mode=state.mode==='demo'?'live':'demo';
  $('demo-banner').hidden=state.mode!=='demo';
  $('demo-toggle').textContent=state.mode==='demo'?'Return to live data':'Explore demo';
  clearData();
  await refresh();
});
$('export').addEventListener('click',()=>{
  if (!state.snapshot) return;
  const payload={...state.snapshot,exported_at:new Date().toISOString(),export_note:'Contains local telemetry. Review before sharing. Internet exposure is unverified.'};
  const url=URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}));
  const anchor=document.createElement('a');
  anchor.href=url;anchor.download=`portlight-${state.mode}-${new Date().toISOString().replace(/[:.]/g,'-')}.json`;
  anchor.click();URL.revokeObjectURL(url);
});
['search','priority-filter','protocol-filter','scope-filter'].forEach(id=>$(id).addEventListener(id==='search'?'input':'change',renderView));
$('clear-filters').addEventListener('click',()=>{
  $('search').value='';['priority-filter','protocol-filter','scope-filter'].forEach(id=>$(id).value='all');renderView();
});
window.addEventListener('hashchange',setView);
setView();refresh();
setInterval(()=>{if(state.auto && !document.hidden) refresh();},5000);
setInterval(updateFreshness,1000);
document.addEventListener('visibilitychange',()=>{if(state.auto && !document.hidden) refresh();});
