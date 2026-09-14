"""
Flask web dashboard — FINAL UPGRADED Triple System
Lead Type Dropdown: Web + Marketing + Power BI / Fabric + AI
Business Type: User can change anytime
"""

import os, csv, io, json, threading, traceback
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, Response
from scraper_pw import scrape_google_maps
from analyzer import analyze_leads
import config

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))
MIN_RESULTS = 1
MAX_RESULTS = 1000
IS_VERCEL = bool(os.environ.get("VERCEL"))
_jobs = {}
_job_counter = 0
_lock = threading.Lock()

def log_error(job_id, error_msg, exc_info=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] JOB {job_id} ERROR: {error_msg}"
    print(log_msg)
    if exc_info:
        print(traceback.format_exc())
    os.makedirs(config.LOG_DIR, exist_ok=True)
    log_file = os.path.join(config.LOG_DIR, f"error_{datetime.now().strftime('%Y%m%d')}.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")
        if exc_info:
            f.write(traceback.format_exc() + "\n\n")

DASHBOARD_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NextGen Analytics — Triple Lead Generator</title>
<style>
:root{--bg:#0f1117;--card:#1a1d27;--accent:#6c63ff;--accent2:#00d2ff;--text:#e4e4e7;--muted:#71717a;--green:#22c55e;--yellow:#eab308;--red:#ef4444;--orange:#f97316;--border:#27272a}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
.container{max-width:1400px;margin:0 auto;padding:24px}
.header{display:flex;align-items:center;justify-content:space-between;margin-bottom:24px;flex-wrap:wrap;gap:16px}
.header h1{font-size:28px;font-weight:700;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.header p{color:var(--muted);font-size:14px;line-height:1.5}
.badge{display:inline-block;padding:4px 10px;border-radius:20px;font-size:11px;font-weight:700;margin-left:8px;vertical-align:middle}
.badge-all{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff}
.search-panel{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:24px;margin-bottom:24px}
.search-row{display:flex;gap:12px;flex-wrap:wrap;align-items:end}
.field{display:flex;flex-direction:column;gap:6px;flex:1;min-width:180px}
.field label{font-size:12px;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:0.5px}
.field input,.field select{padding:11px 14px;border-radius:8px;border:1px solid var(--border);background:var(--bg);color:var(--text);font-size:14px;outline:none}
.field input:focus,.field select:focus{border-color:var(--accent)}
.field select{cursor:pointer}
.btn{padding:11px 24px;border-radius:8px;border:none;font-weight:600;font-size:14px;cursor:pointer;transition:all .2s}
.btn-primary{background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff}
.btn-primary:hover{opacity:0.9;transform:translateY(-1px)}
.btn-primary:disabled{opacity:0.5;cursor:not-allowed;transform:none}
.btn-secondary{background:var(--border);color:var(--text)}
.btn-secondary:hover{background:#333}
.progress-bar-outer{background:var(--border);border-radius:8px;height:8px;margin:16px 0 8px;overflow:hidden;display:none}
.progress-bar-inner{height:100%;border-radius:8px;background:linear-gradient(90deg,var(--accent),var(--accent2));transition:width 0.3s;width:0%}
.progress-text{font-size:13px;color:var(--muted);display:none}
.stats-row{display:flex;gap:16px;margin-bottom:24px;flex-wrap:wrap}
.stat-card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:16px 24px;flex:1;min-width:150px}
.stat-card .num{font-size:28px;font-weight:700}
.stat-card .label{font-size:12px;color:var(--muted);margin-top:4px}
.stat-card.hot .num{color:var(--red)} .stat-card.warm .num{color:var(--orange)} .stat-card.cold .num{color:var(--green)}
.table-container{background:var(--card);border:1px solid var(--border);border-radius:12px;overflow:hidden}
.table-header{display:flex;justify-content:space-between;align-items:center;padding:16px 20px;border-bottom:1px solid var(--border);flex-wrap:wrap;gap:12px}
.table-header h3{font-size:16px}
table{width:100%;border-collapse:collapse}
thead th{text-align:left;padding:12px 16px;font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:0.5px;border-bottom:1px solid var(--border);cursor:pointer;user-select:none}
thead th:hover{color:var(--text)}
tbody td{padding:12px 16px;font-size:13px;border-bottom:1px solid var(--border);vertical-align:top}
tbody tr:hover{background:rgba(108,99,255,0.05)}
.score-badge{display:inline-block;padding:4px 12px;border-radius:20px;font-size:12px;font-weight:700}
.score-hot{background:rgba(239,68,68,0.15);color:var(--red)} .score-warm{background:rgba(249,115,22,0.15);color:var(--orange)}
.score-medium{background:rgba(234,179,8,0.15);color:var(--yellow)} .score-cold{background:rgba(34,197,94,0.15);color:var(--green)}
.type-badge{display:inline-block;padding:3px 8px;border-radius:12px;font-size:10px;font-weight:700;margin-top:4px}
.type-web{background:rgba(108,99,255,0.15);color:#a5a3ff} .type-marketing{background:rgba(249,115,22,0.15);color:var(--orange)}
.type-powerbi{background:rgba(0,210,255,0.15);color:var(--accent2)} .type-ai{background:rgba(34,197,94,0.15);color:var(--green)}
.issues-list{list-style:none} .issues-list li{font-size:12px;color:var(--muted);padding:2px 0}
.issues-list li::before{content:"⚠ ";color:var(--yellow)} .issues-list li.hot-issue{color:var(--text);font-weight:500}
.link{color:var(--accent2);text-decoration:none;font-size:12px} .link:hover{text-decoration:underline}
.no-website{color:var(--red);font-weight:600;font-size:12px} .hidden{display:none}
.filter-tabs{display:flex;gap:8px;flex-wrap:wrap}
.filter-tab{padding:6px 14px;border-radius:6px;font-size:11px;cursor:pointer;border:1px solid var(--border);background:transparent;color:var(--muted)}
.filter-tab.active{background:var(--accent);color:#fff;border-color:var(--accent)}
.error-banner{background:rgba(239,68,68,0.1);border:1px solid var(--red);color:var(--red);padding:12px 16px;border-radius:8px;margin:16px 0;font-size:14px}
.info-box{background:rgba(108,99,255,0.08);border:1px solid var(--border);border-radius:8px;padding:12px 16px;margin-bottom:16px;font-size:13px;color:var(--muted)}
.info-box strong{color:var(--text)}
@media(max-width:768px){.search-row{flex-direction:column}.stats-row{flex-direction:column}.table-container{overflow-x:auto}table{min-width:1000px}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div>
      <h1>🎯 NextGen Analytics <span class="badge badge-all">TRIPLE SYSTEM</span></h1>
      <p>Find <strong>Web Dev</strong> + <strong>Marketing</strong> + <strong>Power BI / Fabric</strong> clients on Google Maps — Change Business Type anytime</p>
    </div>
  </div>
  <div class="info-box">
    💡 <strong>How to use:</strong> Select Lead Type from dropdown → Type any Business (you can change it anytime: e.g. "Real Estate", "Dentists", "Restaurants") → Get hot leads for that specific service.
  </div>
  <div class="search-panel">
    <form id="searchForm" onsubmit="startSearch(event)">
      <div class="search-row">
        <div class="field" style="min-width:220px; flex:0.8">
          <label>🎯 Lead Type (Dropdown)</label>
          <select id="leadType" required>
            {% for opt in lead_type_options %}
            <option value="{{ opt.value }}" {% if opt.value=='all' %}selected{% endif %}>{{ opt.label }}</option>
            {% endfor %}
          </select>
        </div>
        <div class="field">
          <label>Business Type (Tum apne hisaab se change karo)</label>
          <input type="text" id="businessType" placeholder="e.g. Real Estate, Dentists, Restaurants, Car Dealers" required>
        </div>
        <div class="field">
          <label>Location</label>
          <input type="text" id="location" placeholder="e.g. Karachi, Dubai, Miami" required>
        </div>
        <div class="field">
          <label>Country</label>
          <input type="text" id="country" list="countryOptions" value="Pakistan" required>
          <datalist id="countryOptions">{% for c in country_options %}<option value="{{ c }}"></option>{% endfor %}</datalist>
        </div>
        <div class="field" style="max-width:110px">
          <label>Max</label>
          <input type="number" id="maxResults" value="20" min="1" max="1000">
        </div>
        <button type="submit" class="btn btn-primary" id="searchBtn">🔍 Find Leads</button>
      </div>
    </form>
    <div class="progress-bar-outer" id="progressOuter"><div class="progress-bar-inner" id="progressInner"></div></div>
    <div class="progress-text" id="progressText"></div>
    <div id="errorBanner" class="error-banner hidden"></div>
  </div>
  <div class="stats-row hidden" id="statsRow">
    <div class="stat-card"><div class="num" id="statTotal">0</div><div class="label">Total Leads</div></div>
    <div class="stat-card hot"><div class="num" id="statHot">0</div><div class="label">🔥 Hot</div></div>
    <div class="stat-card warm"><div class="num" id="statWarm">0</div><div class="label">🟠 Warm</div></div>
    <div class="stat-card cold"><div class="num" id="statCold">0</div><div class="label">🟢 Low</div></div>
  </div>
  <div class="table-container hidden" id="resultsContainer">
    <div class="table-header">
      <h3 id="resultsTitle">Lead Results</h3>
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
        <div class="filter-tabs">
          <button class="filter-tab active" onclick="filterLeads('all',this)">All</button>
          <button class="filter-tab" onclick="filterLeads('hot',this)">🔥 Hot</button>
          <button class="filter-tab" onclick="filterLeads('web',this)">💻 Web</button>
          <button class="filter-tab" onclick="filterLeads('marketing',this)">📢 Marketing</button>
          <button class="filter-tab" onclick="filterLeads('powerbi',this)">📊 Power BI</button>
        </div>
        <button class="btn btn-secondary" onclick="exportCSV()">📥 Export CSV</button>
      </div>
    </div>
    <table><thead><tr>
      <th onclick="sortTable('lead_score')">#Score + Type</th>
      <th onclick="sortTable('name')">Business</th>
      <th>Category</th><th>Contact</th><th>Email</th><th>Website</th><th>Opportunity</th><th>Maps</th>
    </tr></thead><tbody id="resultsBody"></tbody></table>
  </div>
  <footer style="text-align:center;padding:24px 0 8px;color:var(--muted);font-size:12px">&copy; <span id="footerYear"></span> NextGen Analytics — Triple Lead System</footer>
</div>
<script>
let allLeads=[]; let currentFilter='all'; let pollInterval=null; let currentJobId=null;
document.getElementById('footerYear').textContent=new Date().getFullYear();
async function startSearch(e){
  e.preventDefault();
  const leadType=document.getElementById('leadType').value;
  const biz=document.getElementById('businessType').value.trim();
  const loc=document.getElementById('location').value.trim();
  const country=document.getElementById('country').value.trim();
  const max=Math.min(Math.max(parseInt(document.getElementById('maxResults').value,10)||20,1),1000);
  if(!biz||!loc||!country) return;
  const btn=document.getElementById('searchBtn'); btn.disabled=true; btn.textContent='⏳ Finding...';
  allLeads=[]; currentJobId=null; showProgress(true); hideError(); updateProgress(0,100,'Starting '+leadType+' scan...');
  try{
    const res=await fetch('/api/search',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({business_type:biz, location:loc, country:country, max_results:max, lead_type:leadType})});
    const data=await res.json(); if(!res.ok) throw new Error(data.error||'Search failed');
    if(data.results){ allLeads=data.results||[]; renderLeads(allLeads, leadType); btn.disabled=false; btn.textContent='🔍 Find Leads'; updateProgress(allLeads.length,allLeads.length||1,data.message||'Done'); setTimeout(()=>showProgress(false),500); return; }
    if(data.job_id){ currentJobId=data.job_id; pollInterval=setInterval(()=>pollJob(data.job_id, leadType),1500); }
  }catch(err){ showError('Error: '+err.message); btn.disabled=false; btn.textContent='🔍 Find Leads'; showProgress(false); }
}
async function pollJob(jobId, leadType){
  try{
    const res=await fetch('/api/status/'+jobId); const data=await res.json();
    updateProgress(data.progress||0,data.total||100,data.message||'');
    if(data.status==='done'){ clearInterval(pollInterval); allLeads=data.results||[]; renderLeads(allLeads, leadType); document.getElementById('searchBtn').disabled=false; document.getElementById('searchBtn').textContent='🔍 Find Leads'; setTimeout(()=>showProgress(false),500); }
    else if(data.status==='error'){ clearInterval(pollInterval); showError(data.message||'Error'); document.getElementById('searchBtn').disabled=false; document.getElementById('searchBtn').textContent='🔍 Find Leads'; showProgress(false); }
  }catch(err){ console.error(err); }
}
function showProgress(s){ document.getElementById('progressOuter').style.display=s?'block':'none'; document.getElementById('progressText').style.display=s?'block':'none'; }
function showError(m){ const b=document.getElementById('errorBanner'); b.textContent=m; b.classList.remove('hidden'); }
function hideError(){ document.getElementById('errorBanner').classList.add('hidden'); }
function updateProgress(c,t,msg){ const pct=t>0?Math.round((c/t)*100):0; document.getElementById('progressInner').style.width=pct+'%'; document.getElementById('progressText').textContent=`${c}/${t} — ${msg}`; }
function scoreBadge(lead){
  const s=lead.lead_score||0; let badge=s>=80?`<span class="score-badge score-hot">${s} 🔥</span>`:s>=60?`<span class="score-badge score-warm">${s}</span>`:s>=30?`<span class="score-badge score-medium">${s}</span>`:`<span class="score-badge score-cold">${s}</span>`;
  const label=(lead.opportunity_label||'').toLowerCase(); let typeBadge='';
  if(label.includes('web')) typeBadge+=`<span class="type-badge type-web">💻 WEB</span> `;
  if(label.includes('marketing')) typeBadge+=`<span class="type-badge type-marketing">📢 MKT</span> `;
  if(label.includes('power')) typeBadge+=`<span class="type-badge type-powerbi">📊 POWER BI</span> `;
  if(label.includes('ai')) typeBadge+=`<span class="type-badge type-ai">🤖 AI</span> `;
  if(!typeBadge && lead.lead_type) typeBadge=`<span class="type-badge type-${lead.lead_type}">${lead.lead_type.toUpperCase()}</span>`;
  return badge+'<br>'+typeBadge;
}
function escapeHtml(v){ return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function safeUrl(v){ if(!v) return '#'; try{ const u=new URL(v, window.location.origin); return ['http:','https:'].includes(u.protocol)?u.href:'#'; }catch{ return '#'; } }
function renderLeads(leads, leadType){
  document.getElementById('statsRow').classList.remove('hidden');
  document.getElementById('resultsContainer').classList.remove('hidden');
  document.getElementById('resultsTitle').textContent=`Lead Results — ${leadType.toUpperCase()} (${leads.length})`;
  const hot=leads.filter(l=>l.is_hot_opportunity).length; const warm=leads.filter(l=>(l.lead_score||0)>=50 && (l.lead_score||0)<80).length; const cold=leads.length-hot-warm;
  document.getElementById('statTotal').textContent=leads.length; document.getElementById('statHot').textContent=hot; document.getElementById('statWarm').textContent=warm; document.getElementById('statCold').textContent=cold;
  let filtered=leads;
  if(currentFilter==='hot') filtered=leads.filter(l=>l.is_hot_opportunity);
  else if(currentFilter==='web') filtered=leads.filter(l=>(l.opportunity_label||'').toLowerCase().includes('web')||l.lead_type==='web');
  else if(currentFilter==='marketing') filtered=leads.filter(l=>(l.opportunity_label||'').toLowerCase().includes('marketing')||l.lead_type==='marketing');
  else if(currentFilter==='powerbi') filtered=leads.filter(l=>(l.opportunity_label||'').toLowerCase().includes('power')||l.lead_type==='powerbi');
  const tbody=document.getElementById('resultsBody'); tbody.innerHTML='';
  filtered.forEach(lead=>{
    const r=lead.website_report||{}; let issues=(r.issues||[]).map(i=>`<li>${escapeHtml(i)}</li>`).join('');
    if(lead.extra_issues) issues+=lead.extra_issues.map(i=>`<li class="hot-issue">${escapeHtml(i)}</li>`).join('');
    const websiteCell=lead.website?`<a class="link" href="${escapeHtml(safeUrl(r.url||lead.website))}" target="_blank">${escapeHtml(lead.website)}</a><br><small style="color:var(--muted)">${escapeHtml((r.tech_signals||[]).join(', ')||'')}</small>`:'<span class="no-website">NO WEBSITE</span>';
    const emailCell=lead.email?`<a class="link" href="mailto:${escapeHtml(lead.email)}">${escapeHtml(lead.email)}</a>`:'<small style="color:var(--muted)">N/A</small>';
    tbody.innerHTML+=`<tr><td>${scoreBadge(lead)}</td>
      <td><strong>${escapeHtml(lead.name||'N/A')}</strong><br><small style="color:var(--muted)">${escapeHtml(lead.rating||'')} ★ · ${escapeHtml(lead.reviews||0)} reviews</small></td>
      <td>${escapeHtml(lead.category||'N/A')}</td>
      <td>${escapeHtml(lead.phone||'N/A')}<br><small style="color:var(--muted)">${escapeHtml(lead.address||'')}</small></td>
      <td>${emailCell}</td><td>${websiteCell}</td>
      <td><ul class="issues-list">${issues}</ul></td>
      <td><a class="link" href="${escapeHtml(safeUrl(lead.maps_url))}" target="_blank">📍 Maps</a></td></tr>`;
  });
}
function filterLeads(f,el){ currentFilter=f; document.querySelectorAll('.filter-tab').forEach(t=>t.classList.remove('active')); if(el) el.classList.add('active'); renderLeads(allLeads, document.getElementById('leadType').value); }
function sortTable(k){ allLeads.sort((a,b)=>{ const av=a[k]||''; const bv=b[k]||''; if(typeof av==='number') return bv-av; return String(av).localeCompare(String(bv)); }); renderLeads(allLeads, document.getElementById('leadType').value); }
async function exportCSV(){
  if(!allLeads.length) return alert('No data');
  if(currentJobId){ window.location.href='/api/export/'+encodeURIComponent(currentJobId); return; }
  const res=await fetch('/api/export',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({leads:allLeads})});
  if(!res.ok) return alert('Export failed'); const blob=await res.blob(); const url=URL.createObjectURL(blob);
  const a=document.createElement('a'); a.href=url; a.download='nextgen_triple_leads.csv'; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
}
</script>
</body>
</html>
"""

@app.route("/")
def index():
    lead_opts = getattr(config, 'LEAD_TYPE_OPTIONS', [{"value":"all","label":"All"}])
    country_opts = getattr(config, 'COUNTRY_OPTIONS', getattr(config, 'COUNTRIES', ["Pakistan"]))
    return render_template_string(DASHBOARD_HTML, country_options=country_opts, lead_type_options=lead_opts)

def _parse_max(value):
    try: req=int(value)
    except: req=20
    return max(MIN_RESULTS, min(req, MAX_RESULTS))

def _build_query(biz, loc, country):
    parts=[loc.strip()]
    if country: parts.append(country.strip())
    return f"{biz.strip()} in {', '.join(parts)}"

def _search_and_analyze(query, max_results, country, lead_type, progress_callback=None):
    leads=scrape_google_maps(query, max_results=max_results, progress_callback=progress_callback)
    for lead in leads: 
        lead["country"]=country
        lead["lead_type"]=lead_type
    analyze_leads(leads, lead_type=lead_type, progress_callback=progress_callback)
    return leads

@app.route("/api/search", methods=["POST"])
def api_search():
    global _job_counter
    data=request.get_json(silent=True) or {}
    biz_type=data.get("business_type","").strip()
    location=data.get("location","").strip()
    country=data.get("country","").strip()
    lead_type=data.get("lead_type","all").strip().lower()
    max_results=_parse_max(data.get("max_results",20))
    if not biz_type or not location or not country:
        return jsonify({"error":"business_type, location, country required"}),400
    with _lock:
        _job_counter+=1
        job_id=str(_job_counter)
        _jobs[job_id]={"status":"running","progress":0,"total":max_results,"message":f"Starting {lead_type} scan...","results":[],"business_type":biz_type,"location":location,"country":country,"lead_type":lead_type}
    query=_build_query(biz_type, location, country)
    if IS_VERCEL:
        try:
            leads=_search_and_analyze(query, max_results, country, lead_type)
        except Exception as exc:
            log_error(job_id, f"Vercel failed: {exc}", exc_info=True)
            return jsonify({"error":str(exc)}),500
        return jsonify({"status":"done","message":f"Done! Found {len(leads)} {lead_type} leads.","results":leads})

    def run_job():
        job=_jobs[job_id]
        def on_scrape(cur,tot,msg):
            job["progress"]=cur; job["total"]=tot; job["message"]=f"[Scraping] {msg}"
        try:
            leads=scrape_google_maps(query, max_results=max_results, progress_callback=on_scrape)
            for lead in leads: lead["country"]=country; lead["lead_type"]=lead_type
            job["message"]="Analyzing for "+lead_type+"..."
            job["progress"]=0; job["total"]=len(leads)
            def on_analyze(cur,tot,msg):
                job["progress"]=cur; job["total"]=tot; job["message"]=f"[Analyzing {lead_type}] {msg}"
            analyze_leads(leads, lead_type=lead_type, progress_callback=on_analyze)
            job["results"]=leads; job["status"]="done"
            job["message"]=f"Done! Found {len(leads)} {lead_type} leads ({sum(1 for l in leads if l.get('is_hot_opportunity'))} hot)."
        except Exception as exc:
            log_error(job_id, f"Job failed: {exc}", exc_info=True)
            job["status"]="error"; job["message"]=str(exc)
    threading.Thread(target=run_job, daemon=True).start()
    return jsonify({"job_id":job_id})

@app.route("/api/status/<job_id>")
def api_status(job_id):
    job=_jobs.get(job_id)
    if not job: return jsonify({"error":"Job not found"}),404
    return jsonify(job)

def _csv_response(leads):
    output=io.StringIO()
    writer=csv.writer(output)
    writer.writerow(["Score","Lead_Type","Opportunity","Name","Category","Phone","Email","Address","Country","Website","Rating","Reviews","Issues","Maps URL"])
    for lead in leads:
        report=lead.get("website_report",{})
        writer.writerow([lead.get("lead_score",""), lead.get("lead_type",""), lead.get("opportunity_label",""),
            lead.get("name",""), lead.get("category",""), lead.get("phone",""), lead.get("email","") or "",
            lead.get("address",""), lead.get("country",""), lead.get("website","None"),
            lead.get("rating",""), lead.get("reviews",""),
            " | ".join(report.get("issues",[]))+" | "+" | ".join(lead.get("extra_issues",[])),
            lead.get("maps_url","")])
    timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    lead_type = leads[0].get('lead_type','all') if leads else 'all'
    return Response(output.getvalue(), mimetype="text/csv",
        headers={"Content-Disposition":f"attachment; filename=nextgen_{lead_type}_leads_{timestamp}.csv"})

@app.route("/api/export/<job_id>")
def api_export_job(job_id):
    job=_jobs.get(job_id)
    if not job: return "Job not found",404
    return _csv_response(job.get("results",[]))

@app.route("/api/export", methods=["GET","POST"])
def api_export():
    if request.method=="POST":
        payload=request.get_json(silent=True) or {}
        return _csv_response(payload.get("leads",[]))
    raw=request.args.get("data","[]")
    try: leads=json.loads(raw)
    except: return "Invalid data",400
    return _csv_response(leads)

if __name__=="__main__":
    print(f"\n 🎯 NextGen Triple Lead Generator at http://{config.FLASK_HOST}:{config.FLASK_PORT}\n")
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.FLASK_DEBUG)
