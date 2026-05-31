"""
BuildAdvisor – Full-Suite Web App (Flask)
Tabs: Cost Estimate · Material Calculator · Feasibility Study
Run: python3 app.py  →  http://localhost:5000
"""

from flask import Flask, request, jsonify, render_template_string
from predict import predict_cost
from material_estimator import estimate_materials
from feasibility import analyze_feasibility

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────────────────────
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>BuildAdvisor – Construction Intelligence</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet"/>
<style>
/* ── Reset & Base ────────────────────────────────── */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#080b14;
  --surface:#0e1220;
  --card:#141828;
  --card2:#181d2e;
  --border:#1e2540;
  --border2:#252d48;
  --accent:#5b8dee;
  --accent2:#8b5cf6;
  --accent3:#06b6d4;
  --green:#10d98c;
  --yellow:#f5a623;
  --red:#f87171;
  --text:#e4eaf8;
  --muted:#6b7ba8;
  --muted2:#4a5578;
  --input-bg:#0f1422;
  --r:12px;
  --r2:8px;
}
html{scroll-behavior:smooth}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;overflow-x:hidden}

/* ── Animated background ─────────────────────────── */
body::before{
  content:'';position:fixed;inset:0;z-index:-1;
  background:
    radial-gradient(ellipse 80% 60% at 10% 0%,  rgba(91,141,238,.07) 0%,transparent 60%),
    radial-gradient(ellipse 60% 50% at 90% 100%,rgba(139,92,246,.07) 0%,transparent 60%),
    radial-gradient(ellipse 50% 40% at 50% 50%, rgba(6,182,212,.04)  0%,transparent 70%);
}

/* ── Header ──────────────────────────────────────── */
.topbar{
  display:flex;align-items:center;justify-content:space-between;
  padding:18px 40px;
  background:rgba(14,18,32,.85);backdrop-filter:blur(20px);
  border-bottom:1px solid var(--border);
  position:sticky;top:0;z-index:100;
}
.logo{display:flex;align-items:center;gap:12px}
.logo-icon{
  width:40px;height:40px;border-radius:10px;
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  display:flex;align-items:center;justify-content:center;font-size:20px;
  box-shadow:0 4px 20px rgba(91,141,238,.35);
}
.logo-text h1{font-size:1.15rem;font-weight:800;letter-spacing:-.02em}
.logo-text p{font-size:.72rem;color:var(--muted);letter-spacing:.05em;text-transform:uppercase}
.badge{
  font-size:.72rem;font-weight:600;padding:4px 12px;border-radius:20px;
  background:linear-gradient(135deg,rgba(91,141,238,.15),rgba(139,92,246,.15));
  border:1px solid rgba(91,141,238,.25);color:var(--accent);
}

/* ── Main layout ─────────────────────────────────── */
.layout{display:grid;grid-template-columns:340px 1fr;gap:0;min-height:calc(100vh - 73px)}

/* ── Sidebar ─────────────────────────────────────── */
.sidebar{
  background:var(--surface);border-right:1px solid var(--border);
  padding:28px 24px;position:sticky;top:73px;height:calc(100vh - 73px);
  overflow-y:auto;
}
.sidebar-title{font-size:.72rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;margin-bottom:20px}

.field{margin-bottom:16px}
.field label{display:block;font-size:.75rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px}
.field input[type=number]{
  width:100%;background:var(--input-bg);border:1px solid var(--border2);
  border-radius:var(--r2);color:var(--text);font-family:inherit;font-size:.93rem;
  padding:10px 13px;outline:none;transition:border-color .2s,box-shadow .2s;
}
.field input[type=number]:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(91,141,238,.12)}

/* slider */
.slider-wrap{display:flex;align-items:center;gap:10px}
.slider-wrap input[type=range]{flex:1;accent-color:var(--accent);cursor:pointer;height:4px}
.slider-val{font-size:.9rem;font-weight:700;color:var(--accent);min-width:36px;text-align:right}

/* pills */
.pills{display:flex;flex-wrap:wrap;gap:6px}
.pills input{display:none}
.pills label{
  font-size:.78rem;font-weight:600;padding:6px 13px;border:1px solid var(--border2);
  border-radius:20px;background:var(--input-bg);color:var(--muted);cursor:pointer;
  transition:all .18s;user-select:none;
}
.pills input:checked+label{
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  border-color:transparent;color:#fff;
  box-shadow:0 2px 14px rgba(91,141,238,.3);
}
.pills label:hover:not(.checked){border-color:var(--accent);color:var(--text)}

.sep{height:1px;background:var(--border);margin:20px 0}

.calc-btn{
  width:100%;padding:13px;
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  border:none;border-radius:var(--r);color:#fff;
  font-family:inherit;font-size:.97rem;font-weight:700;
  cursor:pointer;transition:opacity .2s,transform .15s;letter-spacing:.02em;
  position:relative;overflow:hidden;
}
.calc-btn::after{
  content:'';position:absolute;inset:0;
  background:linear-gradient(135deg,transparent,rgba(255,255,255,.1),transparent);
  transform:translateX(-100%);transition:transform .5s;
}
.calc-btn:hover::after{transform:translateX(100%)}
.calc-btn:hover{opacity:.9;transform:translateY(-1px)}
.calc-btn:active{transform:translateY(0)}
.calc-btn.loading{opacity:.6;pointer-events:none}

.error-msg{
  margin-top:12px;padding:10px 13px;border-radius:var(--r2);
  background:rgba(248,113,113,.1);border:1px solid rgba(248,113,113,.3);
  color:#f87171;font-size:.83rem;display:none;
}
.error-msg.show{display:block}

/* ── Content pane ────────────────────────────────── */
.content{padding:32px 36px;overflow-y:auto}

/* ── Tabs ────────────────────────────────────────── */
.tabs{display:flex;gap:4px;margin-bottom:28px;
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--r);padding:5px;width:fit-content;
}
.tab-btn{
  padding:9px 22px;border-radius:9px;border:none;
  background:transparent;color:var(--muted);
  font-family:inherit;font-size:.87rem;font-weight:600;cursor:pointer;
  transition:all .2s;white-space:nowrap;
}
.tab-btn.active{
  background:linear-gradient(135deg,rgba(91,141,238,.2),rgba(139,92,246,.2));
  color:var(--text);border:1px solid rgba(91,141,238,.25);
}
.tab-pane{display:none;animation:fadeUp .35s ease}
.tab-pane.active{display:block}

/* ── Idle state ──────────────────────────────────── */
.idle{
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  min-height:420px;gap:16px;opacity:.45;
}
.idle-icon{font-size:56px}
.idle p{font-size:.95rem;color:var(--muted);text-align:center;max-width:280px;line-height:1.6}

/* ── Cost tab ────────────────────────────────────── */
.cost-hero{
  background:linear-gradient(135deg,rgba(91,141,238,.1),rgba(139,92,246,.1));
  border:1px solid rgba(91,141,238,.2);border-radius:16px;
  padding:32px;text-align:center;margin-bottom:24px;
}
.cost-label{font-size:.75rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.1em}
.cost-amount{
  font-size:3rem;font-weight:900;
  background:linear-gradient(135deg,var(--green),#06d6a0);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  line-height:1.1;margin:8px 0;
}
.cost-sub{font-size:.88rem;color:var(--muted);line-height:1.7}
.cost-sub span{color:var(--text);font-weight:600}

.stat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:24px}
.stat-card{
  background:var(--card);border:1px solid var(--border);border-radius:var(--r);
  padding:18px;text-align:center;
}
.stat-card .s-val{font-size:1.3rem;font-weight:800;color:var(--accent)}
.stat-card .s-lbl{font-size:.73rem;color:var(--muted);margin-top:4px;font-weight:500}

/* ── Materials tab ───────────────────────────────── */
.mat-section{margin-bottom:24px}
.mat-section-title{
  display:flex;align-items:center;gap:10px;
  font-size:.85rem;font-weight:700;color:var(--muted);text-transform:uppercase;
  letter-spacing:.08em;margin-bottom:14px;
}
.mat-section-title span{
  display:inline-block;width:28px;height:28px;border-radius:7px;
  font-size:14px;display:flex;align-items:center;justify-content:center;
}
.mat-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px}
.mat-card{
  background:var(--card);border:1px solid var(--border);border-radius:var(--r);
  padding:16px 14px;transition:border-color .2s,transform .2s;
}
.mat-card:hover{border-color:var(--border2);transform:translateY(-2px)}
.mat-card .m-icon{font-size:22px;margin-bottom:8px}
.mat-card .m-val{font-size:1.3rem;font-weight:800;color:var(--text)}
.mat-card .m-unit{font-size:.72rem;color:var(--accent);font-weight:600;margin-left:3px}
.mat-card .m-lbl{font-size:.75rem;color:var(--muted);margin-top:4px;line-height:1.4}

/* ── Feasibility tab ─────────────────────────────── */
.feas-hero{
  display:grid;grid-template-columns:auto 1fr;gap:28px;align-items:center;
  background:var(--card);border:1px solid var(--border);border-radius:16px;
  padding:28px;margin-bottom:24px;
}
.score-ring{position:relative;width:130px;height:130px;flex-shrink:0}
.score-ring svg{transform:rotate(-90deg)}
.score-ring .ring-bg{fill:none;stroke:var(--border2);stroke-width:10}
.score-ring .ring-fg{fill:none;stroke-width:10;stroke-linecap:round;transition:stroke-dashoffset 1.2s ease}
.score-center{
  position:absolute;inset:0;display:flex;flex-direction:column;
  align-items:center;justify-content:center;
}
.score-num{font-size:1.9rem;font-weight:900}
.score-lbl{font-size:.68rem;color:var(--muted);font-weight:600;letter-spacing:.05em;text-transform:uppercase}

.risk-badge{
  display:inline-flex;align-items:center;gap:6px;padding:5px 14px;
  border-radius:20px;font-size:.82rem;font-weight:700;margin-bottom:12px;
}
.feas-hero-right h2{font-size:1.2rem;font-weight:800;margin-bottom:6px}
.feas-hero-right p{font-size:.87rem;color:var(--muted);line-height:1.6}

.sub-scores{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:24px}
.sub-card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:16px}
.sub-card .sc-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.sub-card .sc-name{font-size:.8rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
.sub-card .sc-val{font-size:1rem;font-weight:800}
.progress-bar{height:5px;background:var(--border2);border-radius:3px;overflow:hidden}
.progress-fill{height:100%;border-radius:3px;transition:width 1s ease}

.alerts-section{margin-bottom:20px}
.alert-item{
  display:flex;gap:12px;padding:13px 15px;border-radius:var(--r2);
  margin-bottom:10px;font-size:.86rem;line-height:1.6;
}
.alert-item.issue{background:rgba(248,113,113,.08);border:1px solid rgba(248,113,113,.25);color:#fca5a5}
.alert-item.warning{background:rgba(245,166,35,.08);border:1px solid rgba(245,166,35,.25);color:#fcd34d}
.alert-item.reco{background:rgba(16,217,140,.08);border:1px solid rgba(16,217,140,.2);color:#6ee7b7}
.alert-icon{font-size:16px;flex-shrink:0;margin-top:1px}

.site-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px}
.site-card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:16px}
.site-card .sv{font-size:1.1rem;font-weight:800;color:var(--accent3)}
.site-card .sl{font-size:.75rem;color:var(--muted);margin-top:4px}

.budget-row{
  display:grid;grid-template-columns:repeat(4,1fr);gap:12px;
}
.budget-card{
  background:var(--card);border:1px solid var(--border);border-radius:var(--r);
  padding:16px;text-align:center;
}
.budget-card .bv{font-size:1rem;font-weight:800;color:var(--text)}
.budget-card .bl{font-size:.72rem;color:var(--muted);margin-top:4px}
.budget-card.highlight{
  background:linear-gradient(135deg,rgba(16,217,140,.08),rgba(6,182,212,.08));
  border-color:rgba(16,217,140,.25);
}
.budget-card.highlight .bv{color:var(--green)}

.section-hdr{
  font-size:.75rem;font-weight:700;color:var(--muted);text-transform:uppercase;
  letter-spacing:.1em;margin-bottom:14px;margin-top:24px;display:flex;align-items:center;gap:8px;
}
.section-hdr::after{content:'';flex:1;height:1px;background:var(--border)}

@keyframes fadeUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
@keyframes countUp{from{opacity:0}to{opacity:1}}

/* ── Responsive ──────────────────────────────────── */
@media(max-width:900px){
  .layout{grid-template-columns:1fr}
  .sidebar{position:relative;height:auto;top:0}
  .content{padding:24px 20px}
  .stat-grid{grid-template-columns:repeat(2,1fr)}
  .sub-scores{grid-template-columns:1fr}
  .site-grid{grid-template-columns:repeat(2,1fr)}
  .budget-row{grid-template-columns:repeat(2,1fr)}
  .feas-hero{grid-template-columns:1fr}
}
</style>
</head>
<body>

<!-- ── Top bar ──────────────────────────────────── -->
<header class="topbar">
  <div class="logo">
    <div class="logo-icon">🏗️</div>
    <div class="logo-text">
      <h1>BuildAdvisor</h1>
      <p>Construction Intelligence Platform</p>
    </div>
  </div>
  <span class="badge">AI-Powered · Pakistan</span>
</header>

<!-- ── Layout ────────────────────────────────────── -->
<div class="layout">

  <!-- ── Sidebar ──────────────────────────────── -->
  <aside class="sidebar">
    <div class="sidebar-title">Project Details</div>

    <div class="field">
      <label>Total Area (sqft)</label>
      <input type="number" id="area" placeholder="e.g. 1200" min="100"/>
    </div>
    <div class="field">
      <label>Number of Floors</label>
      <input type="number" id="floors" placeholder="e.g. 2" min="1" max="25"/>
    </div>
    <div class="field">
      <label>Number of Rooms</label>
      <input type="number" id="rooms" placeholder="e.g. 3" min="1" max="50"/>
    </div>
    <div class="field">
      <label>Number of Bathrooms</label>
      <input type="number" id="baths" placeholder="e.g. 2" min="1" max="20"/>
    </div>

    <div class="field">
      <label>Location Factor &nbsp;<span id="loc-val" style="color:var(--accent);font-weight:700">1.00</span></label>
      <div class="slider-wrap">
        <span style="font-size:.75rem;color:var(--muted2)">1.0</span>
        <input type="range" id="location" min="1.0" max="1.3" step="0.05" value="1.0"
          oninput="document.getElementById('loc-val').textContent=parseFloat(this.value).toFixed(2)"/>
        <span style="font-size:.75rem;color:var(--muted2)">1.3</span>
      </div>
    </div>

    <div class="sep"></div>

    <div class="field">
      <label>Construction Type</label>
      <div class="pills">
        <input type="radio" name="ct" id="ct-res" value="residential" checked/><label for="ct-res">🏠 Residential</label>
        <input type="radio" name="ct" id="ct-com" value="commercial"/><label for="ct-com">🏢 Commercial</label>
      </div>
    </div>
    <div class="field">
      <label>Quality Level</label>
      <div class="pills">
        <input type="radio" name="ql" id="ql-bas" value="basic"/><label for="ql-bas">🔨 Basic</label>
        <input type="radio" name="ql" id="ql-std" value="standard" checked/><label for="ql-std">⭐ Standard</label>
        <input type="radio" name="ql" id="ql-prm" value="premium"/><label for="ql-prm">💎 Premium</label>
      </div>
    </div>
    <div class="field">
      <label>Structure Type</label>
      <div class="pills">
        <input type="radio" name="st" id="st-brk" value="brick" checked/><label for="st-brk">🧱 Brick</label>
        <input type="radio" name="st" id="st-con" value="concrete"/><label for="st-con">🏗️ Concrete</label>
        <input type="radio" name="st" id="st-stl" value="steel"/><label for="st-stl">⚙️ Steel</label>
      </div>
    </div>

    <div class="field">
      <label>Soil Type</label>
      <div class="pills">
        <input type="radio" name="soil" id="soil-cly" value="clay" checked/><label for="soil-cly">🧱 Clay</label>
        <input type="radio" name="soil" id="soil-snd" value="sand"/><label for="soil-snd">⏳ Sand</label>
        <input type="radio" name="soil" id="soil-grv" value="gravel"/><label for="soil-grv">🪨 Gravel</label>
        <input type="radio" name="soil" id="soil-rck" value="rock"/><label for="soil-rck">💎 Rock</label>
        <input type="radio" name="soil" id="soil-slt" value="silt"/><label for="soil-slt">🌫️ Silt</label>
      </div>
    </div>

    <div class="field">
      <label>Avg Summer Temp &nbsp;<span id="sum-val" style="color:var(--accent);font-weight:700">35.0°C</span></label>
      <div class="slider-wrap">
        <span style="font-size:.75rem;color:var(--muted2)">25°</span>
        <input type="range" id="temp-summer" min="25.0" max="50.0" step="0.5" value="35.0"
          oninput="document.getElementById('sum-val').textContent=parseFloat(this.value).toFixed(1)+'°C'"/>
        <span style="font-size:.75rem;color:var(--muted2)">50°</span>
      </div>
    </div>

    <div class="field">
      <label>Avg Winter Temp &nbsp;<span id="win-val" style="color:var(--accent);font-weight:700">10.0°C</span></label>
      <div class="slider-wrap">
        <span style="font-size:.75rem;color:var(--muted2)">-10°</span>
        <input type="range" id="temp-winter" min="-10.0" max="25.0" step="0.5" value="10.0"
          oninput="document.getElementById('win-val').textContent=parseFloat(this.value).toFixed(1)+'°C'"/>
        <span style="font-size:.75rem;color:var(--muted2)">25°</span>
      </div>
    </div>

    <div class="sep"></div>

    <button class="calc-btn" id="calc-btn" onclick="runAll()">
      ✦ &nbsp;Analyze Project
    </button>
    <div class="error-msg" id="err-msg"></div>
  </aside>

  <!-- ── Content ───────────────────────────────── -->
  <main class="content">

    <!-- Tabs -->
    <div class="tabs">
      <button class="tab-btn active" onclick="showTab('cost',this)">💰 Cost Estimate</button>
      <button class="tab-btn" onclick="showTab('mats',this)">🧱 Materials</button>
      <button class="tab-btn" onclick="showTab('feas',this)">📋 Feasibility</button>
    </div>

    <!-- ── Cost tab ───────────────────────── -->
    <div id="tab-cost" class="tab-pane active">
      <div id="cost-idle" class="idle">
        <div class="idle-icon">💰</div>
        <p>Fill in your project details and click <strong>Analyze Project</strong> to get an AI-powered cost estimate.</p>
      </div>
      <div id="cost-result" style="display:none">
        <div class="cost-hero">
          <div class="cost-label">AI Predicted Construction Cost</div>
          <div class="cost-amount" id="r-cost">—</div>
          <div class="cost-sub" id="r-costsub"></div>
        </div>
        <div class="stat-grid">
          <div class="stat-card">
            <div class="s-val" id="r-psf">—</div>
            <div class="s-lbl">Cost per sqft</div>
          </div>
          <div class="stat-card">
            <div class="s-val" id="r-area">—</div>
            <div class="s-lbl">Total Area</div>
          </div>
          <div class="stat-card">
            <div class="s-val" id="r-floors">—</div>
            <div class="s-lbl">Floors</div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Materials tab ──────────────────── -->
    <div id="tab-mats" class="tab-pane">
      <div id="mats-idle" class="idle">
        <div class="idle-icon">🧱</div>
        <p>Analyze your project to see a full material quantity breakdown for procurement planning.</p>
      </div>
      <div id="mats-result" style="display:none">
        <div class="mat-section">
          <div class="mat-section-title">
            <span style="background:rgba(91,141,238,.15)">🏛️</span>
            Structural Materials
          </div>
          <div class="mat-grid" id="mat-structural"></div>
        </div>
        <div class="mat-section">
          <div class="mat-section-title">
            <span style="background:rgba(16,217,140,.15)">✨</span>
            Finishing Materials
          </div>
          <div class="mat-grid" id="mat-finishing"></div>
        </div>
        <div class="mat-section">
          <div class="mat-section-title">
            <span style="background:rgba(245,166,35,.15)">⚡</span>
            MEP (Mechanical, Electrical & Plumbing)
          </div>
          <div class="mat-grid" id="mat-mep"></div>
        </div>
      </div>
    </div>

    <!-- ── Feasibility tab ────────────────── -->
    <div id="tab-feas" class="tab-pane">
      <div id="feas-idle" class="idle">
        <div class="idle-icon">📋</div>
        <p>Get a full feasibility study: structural limits, zoning rules, site requirements, and sustainability score.</p>
      </div>
      <div id="feas-result" style="display:none">

        <!-- Hero score -->
        <div class="feas-hero">
          <div class="score-ring">
            <svg width="130" height="130" viewBox="0 0 130 130">
              <circle class="ring-bg" cx="65" cy="65" r="55"/>
              <circle class="ring-fg" id="ring-fg" cx="65" cy="65" r="55"
                stroke-dasharray="345.4" stroke-dashoffset="345.4"/>
            </svg>
            <div class="score-center">
              <div class="score-num" id="feas-score-num">0</div>
              <div class="score-lbl">/ 100</div>
            </div>
          </div>
          <div class="feas-hero-right">
            <div class="risk-badge" id="risk-badge">—</div>
            <h2 id="feas-title">Project Feasibility</h2>
            <p id="feas-summary"></p>
          </div>
        </div>

        <!-- Sub-scores -->
        <div class="sub-scores" id="sub-scores"></div>

        <!-- Budget range -->
        <div class="section-hdr">Budget Range</div>
        <div class="budget-row" id="budget-row"></div>

        <!-- Site data -->
        <div class="section-hdr">Site & Structural Data</div>
        <div class="site-grid" id="site-grid"></div>

        <!-- Issues -->
        <div id="issues-section"></div>
        <div id="warns-section"></div>
        <div id="recos-section"></div>

      </div>
    </div>

  </main>
</div>

<script>
// ── Tab switching ───────────────────────────────────────────────
function showTab(id, btn) {
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + id).classList.add('active');
  btn.classList.add('active');
}

// ── Material icons ──────────────────────────────────────────────
const matIcons = {
  "Cement Bags (50 kg)": "🪨",
  "Sand (cubic ft)":     "🏖️",
  "Aggregate (cubic ft)":"🪵",
  "Bricks":              "🧱",
  "Steel Bars (kg)":     "⚙️",
  "Paint (litres)":      "🎨",
  "Tiles (sqft)":        "🟦",
  "Doors":               "🚪",
  "Windows":             "🪟",
  "Glass (sqft)":        "✨",
  "Electrical Wire (m)": "⚡",
  "Switchboards":        "🔌",
  "MCB Breakers":        "🔒",
  "PVC Pipe (m)":        "💧",
  "Sanitary Units":      "🚿",
  "Water Tank (gallons)":"🪣",
};

function fmtNum(n) {
  if (n >= 1000000) return (n/1000000).toFixed(2) + 'M';
  if (n >= 1000)    return (n/1000).toFixed(1) + 'K';
  return n.toLocaleString();
}

// ── Validation ──────────────────────────────────────────────────
function getInputs() {
  const area   = parseFloat(document.getElementById('area').value);
  const floors = parseInt(document.getElementById('floors').value);
  const rooms  = parseInt(document.getElementById('rooms').value);
  const baths  = parseInt(document.getElementById('baths').value);
  const loc    = parseFloat(document.getElementById('location').value);
  const ct     = document.querySelector('input[name=ct]:checked').value;
  const ql     = document.querySelector('input[name=ql]:checked').value;
  const st     = document.querySelector('input[name=st]:checked').value;
  const soil   = document.querySelector('input[name=soil]:checked').value;
  const summer = parseFloat(document.getElementById('temp-summer').value);
  const winter = parseFloat(document.getElementById('temp-winter').value);

  if (!area || area < 100)      throw new Error("Total Area must be ≥ 100 sqft.");
  if (!floors || floors < 1)    throw new Error("Floors must be ≥ 1.");
  if (!rooms || rooms < 1)      throw new Error("Rooms must be ≥ 1.");
  if (!baths || baths < 1)      throw new Error("Bathrooms must be ≥ 1.");

  return { total_area_sqft: area, number_of_floors: floors,
           number_of_rooms: rooms, number_of_bathrooms: baths,
           location_factor: loc, construction_type: ct,
           quality_level: ql, structure_type: st,
           soil_type: soil, avg_temp_summer: summer, avg_temp_winter: winter };
}

// ── Main action ─────────────────────────────────────────────────
async function runAll() {
  const btn = document.getElementById('calc-btn');
  const err = document.getElementById('err-msg');
  err.classList.remove('show');

  let data;
  try { data = getInputs(); }
  catch(e) { err.textContent = '⚠️ ' + e.message; err.classList.add('show'); return; }

  btn.textContent = 'Analyzing…';
  btn.classList.add('loading');

  try {
    const resp = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    const res = await resp.json();
    if (!resp.ok) { err.textContent = '⚠️ ' + (res.error || 'Server error'); err.classList.add('show'); return; }

    renderCost(res.cost, data);
    renderMaterials(res.materials);
    renderFeasibility(res.feasibility);

  } catch(e) {
    err.textContent = '⚠️ Connection error — is the server running?';
    err.classList.add('show');
  } finally {
    btn.textContent = '✦  Analyze Project';
    btn.classList.remove('loading');
  }
}

// ── Render: Cost ────────────────────────────────────────────────
function renderCost(cost, data) {
  document.getElementById('cost-idle').style.display = 'none';
  document.getElementById('cost-result').style.display = 'block';

  document.getElementById('r-cost').textContent = cost.formatted;
  document.getElementById('r-costsub').innerHTML =
    `<span>${data.quality_level.charAt(0).toUpperCase()+data.quality_level.slice(1)}</span> quality &nbsp;·&nbsp; ` +
    `<span>${data.structure_type.charAt(0).toUpperCase()+data.structure_type.slice(1)}</span> structure &nbsp;·&nbsp; ` +
    `<span>${data.soil_type.charAt(0).toUpperCase()+data.soil_type.slice(1)}</span> soil &nbsp;·&nbsp; ` +
    `${data.avg_temp_summer.toFixed(0)}°C/${data.avg_temp_winter.toFixed(0)}°C &nbsp;·&nbsp; ` +
    `Location ×<span>${data.location_factor.toFixed(2)}</span>`;

  const psf = Math.round(cost.predicted_cost_pkr / data.total_area_sqft);
  document.getElementById('r-psf').textContent  = 'PKR ' + psf.toLocaleString();
  document.getElementById('r-area').textContent  = data.total_area_sqft.toLocaleString() + ' sqft';
  document.getElementById('r-floors').textContent = data.number_of_floors + ' floor(s)';
}

// ── Render: Materials ───────────────────────────────────────────
function renderMaterials(mats) {
  document.getElementById('mats-idle').style.display   = 'none';
  document.getElementById('mats-result').style.display = 'block';

  function renderGroup(id, group) {
    const el = document.getElementById(id);
    el.innerHTML = '';
    for (const [name, val] of Object.entries(group)) {
      const icon = matIcons[name] || '📦';
      const parts = name.match(/^(.+?)\s*\((.+?)\)$/) || [null, name, ''];
      const label = parts[1].trim(), unit = parts[2];
      el.innerHTML += `
        <div class="mat-card">
          <div class="m-icon">${icon}</div>
          <div><span class="m-val">${fmtNum(val)}</span><span class="m-unit">${unit}</span></div>
          <div class="m-lbl">${label}</div>
        </div>`;
    }
  }
  renderGroup('mat-structural', mats.structural);
  renderGroup('mat-finishing',  mats.finishing);
  renderGroup('mat-mep',        mats.mep);
}

// ── Render: Feasibility ─────────────────────────────────────────
function renderFeasibility(f) {
  document.getElementById('feas-idle').style.display   = 'none';
  document.getElementById('feas-result').style.display = 'block';

  // Ring
  const circ = 2 * Math.PI * 55;
  const offset = circ * (1 - f.overall_score / 100);
  const ring = document.getElementById('ring-fg');
  ring.style.stroke = f.risk_color;
  ring.style.strokeDashoffset = circ;   // start at 0
  setTimeout(() => { ring.style.strokeDashoffset = offset; }, 80);

  document.getElementById('feas-score-num').textContent = f.overall_score;
  document.getElementById('feas-score-num').style.color = f.risk_color;

  // Risk badge
  const rb = document.getElementById('risk-badge');
  rb.textContent = f.risk_emoji + '  ' + f.risk_level + ' RISK';
  rb.style.background = f.risk_color + '20';
  rb.style.border = '1px solid ' + f.risk_color + '50';
  rb.style.color = f.risk_color;

  document.getElementById('feas-title').textContent = f.overall_score >= 78
    ? 'Project is Feasible' : f.overall_score >= 55
    ? 'Project Needs Review' : 'Significant Concerns Detected';
  document.getElementById('feas-summary').textContent =
    `Overall feasibility score: ${f.overall_score}/100. `+
    (f.issues.length ? `${f.issues.length} critical issue(s) found. ` : 'No critical structural issues. ')+
    (f.warnings.length ? `${f.warnings.length} warning(s) to review.` : '');

  // Sub-scores
  const subColors = { Structural:'#5b8dee', Zoning:'#8b5cf6', Budget:'#10d98c', Environmental:'#06b6d4' };
  const ss = document.getElementById('sub-scores');
  ss.innerHTML = '';
  for (const [name, val] of Object.entries(f.scores)) {
    const c = subColors[name] || '#5b8dee';
    ss.innerHTML += `
      <div class="sub-card">
        <div class="sc-head">
          <span class="sc-name">${name}</span>
          <span class="sc-val" style="color:${c}">${val}</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" style="width:${val}%;background:${c}"></div>
        </div>
      </div>`;
  }

  // Budget
  const br = document.getElementById('budget-row');
  const b = f.budget;
  br.innerHTML = `
    <div class="budget-card"><div class="bv">PKR ${(b.low_estimate/1e6).toFixed(2)}M</div><div class="bl">Low Estimate</div></div>
    <div class="budget-card highlight"><div class="bv">PKR ${(b.predicted/1e6).toFixed(2)}M</div><div class="bl">AI Predicted</div></div>
    <div class="budget-card"><div class="bv">PKR ${(b.high_estimate/1e6).toFixed(2)}M</div><div class="bl">High Estimate</div></div>
    <div class="budget-card"><div class="bv">PKR ${b.monthly_installment.toLocaleString()}</div><div class="bl">Monthly (10yr @ 15%)</div></div>`;

  // Site grid
  const sg = document.getElementById('site-grid');
  const s = f.site;
  sg.innerHTML = `
    <div class="site-card"><div class="sv">${s.building_height_ft} ft</div><div class="sl">Building Height</div></div>
    <div class="site-card"><div class="sv">${s.foundation_depth_ft} ft</div><div class="sl">Foundation Depth</div></div>
    <div class="site-card"><div class="sv">${s.setback_required_ft} ft</div><div class="sl">Required Setback</div></div>
    <div class="site-card"><div class="sv">${s.max_coverage_pct}%</div><div class="sl">Max Plot Coverage</div></div>
    <div class="site-card"><div class="sv" style="font-size:.85rem">${s.soil_test_required ? '✅ Required' : '➖ Optional'}</div><div class="sl">Soil SBC Test</div></div>
    <div class="site-card"><div class="sv" style="font-size:.78rem;color:var(--text)">${s.structure_system}</div><div class="sl">Structure System</div></div>`;

  // Alerts
  function renderAlerts(id, items, cls, icon, title) {
    const el = document.getElementById(id);
    if (!items.length) { el.innerHTML = ''; return; }
    el.innerHTML = `<div class="section-hdr">${title}</div>` +
      items.map(t => `<div class="alert-item ${cls}"><span class="alert-icon">${icon}</span>${t}</div>`).join('');
  }
  renderAlerts('issues-section', f.issues,       'issue',   '🚨', 'Critical Issues');
  renderAlerts('warns-section',  f.warnings,     'warning', '⚠️', 'Warnings');
  renderAlerts('recos-section',  f.recommendations,'reco',  '💡', 'Recommendations');
}

// Keyboard shortcut
document.addEventListener('keydown', e => { if (e.key === 'Enter' && e.ctrlKey) runAll(); });
</script>
</body>
</html>
"""

# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(force=True)
    try:
        cost = predict_cost(data)

        mats = estimate_materials(
            total_area_sqft     = data["total_area_sqft"],
            number_of_floors    = data["number_of_floors"],
            number_of_rooms     = data["number_of_rooms"],
            number_of_bathrooms = data["number_of_bathrooms"],
            construction_type   = data["construction_type"],
            quality_level       = data["quality_level"],
            structure_type      = data["structure_type"],
            soil_type           = data["soil_type"],
            avg_temp_summer     = data["avg_temp_summer"],
            avg_temp_winter     = data["avg_temp_winter"],
        )

        feas = analyze_feasibility(
            total_area_sqft     = data["total_area_sqft"],
            number_of_floors    = data["number_of_floors"],
            number_of_rooms     = data["number_of_rooms"],
            number_of_bathrooms = data["number_of_bathrooms"],
            location_factor     = data["location_factor"],
            construction_type   = data["construction_type"],
            quality_level       = data["quality_level"],
            structure_type      = data["structure_type"],
            predicted_cost      = cost["predicted_cost_pkr"],
            soil_type           = data["soil_type"],
            avg_temp_summer     = data["avg_temp_summer"],
            avg_temp_winter     = data["avg_temp_winter"],
        )

        return {"cost": cost, "materials": mats, "feasibility": feas}

    except (ValueError, KeyError) as e:
        return {"error": str(e)}, 400


if __name__ == "__main__":
    print("\n  +--------------------------------------+")
    print("  |   BuildAdvisor - Full Suite v2.0     |")
    print("  |   http://localhost:5000              |")
    print("  +--------------------------------------+\n")
    app.run(debug=False, port=5000)
