// ── State ──
let history = JSON.parse(localStorage.getItem('thyro_history')||'[]');
let customRanges = JSON.parse(localStorage.getItem('thyro_ranges')||'null');
let trendChart = null, lastResult = null;
const DEFAULTS = {tsh_low:.4,tsh_high:4.5,t3_low:.8,t3_high:2.0,t4_low:58,t4_high:161};

// ── Theme ──
function toggleTheme(){
  const t=document.documentElement.dataset.theme==='light'?'dark':'light';
  document.documentElement.dataset.theme=t;
  localStorage.setItem('thyro_theme',t);
  document.getElementById('theme-btn').textContent=t==='dark'?'☀️ Light':'🌙 Dark';
  if(trendChart)updateTrendChart();
}
(function(){const t=localStorage.getItem('thyro_theme')||'dark';document.documentElement.dataset.theme=t;})();

// ── Presets ──
function setPreset(tsh,t3,t4){
  document.getElementById('tsh').value=tsh;document.getElementById('t3').value=t3;document.getElementById('t4').value=t4;
  document.getElementById('tsh-slider').value=tsh;document.getElementById('t3-slider').value=t3;document.getElementById('t4-slider').value=t4;
  colorInputs();
}

// ── Slider sync ──
function syncSlider(id){const v=document.getElementById(id);const s=document.getElementById(id+'-slider');s.value=v.value;colorInputs();}
function syncInput(id){const s=document.getElementById(id+'-slider');const v=document.getElementById(id);v.value=s.value;colorInputs();}

// ── Live color coding ──
function colorInputs(){
  const r=customRanges||DEFAULTS;
  colorOne('tsh',r.tsh_low,r.tsh_high);colorOne('t3',r.t3_low,r.t3_high);colorOne('t4',r.t4_low,r.t4_high);
}
function colorOne(id,lo,hi){
  const el=document.getElementById(id);if(!el.value)return el.classList.remove('abnormal','normal-val');
  const v=parseFloat(el.value);
  if(v<lo||v>hi){el.classList.add('abnormal');el.classList.remove('normal-val')}
  else{el.classList.add('normal-val');el.classList.remove('abnormal')}
}

// ── Ripple ──
function ripple(e){
  const btn=e.currentTarget,r=document.createElement('span');r.className='ripple';
  const rect=btn.getBoundingClientRect();r.style.left=(e.clientX-rect.left)+'px';r.style.top=(e.clientY-rect.top)+'px';
  btn.appendChild(r);setTimeout(()=>r.remove(),600);
}

// ── Predict ──
async function predict(e){
  if(e)ripple(e);
  const tsh=document.getElementById('tsh').value,t3=document.getElementById('t3').value,t4=document.getElementById('t4').value;
  const errEl=document.getElementById('error-msg'),btn=document.getElementById('submit-btn');
  errEl.style.display='none';
  if(!tsh||!t3||!t4){errEl.textContent='Please fill in all three values.';errEl.style.display='block';return}
  btn.disabled=true;btn.textContent='Analysing...';
  const symptoms=[...document.querySelectorAll('.symptom-check:checked')].map(c=>c.value);
  try{
    const res=await fetch('/predict',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({tsh:+tsh,t3:+t3,t4:+t4,symptoms,custom_ranges:customRanges})});
    const data=await res.json();
    if(data.error){errEl.textContent=data.error;errEl.style.display='block';return}
    lastResult=data;showResult(data);saveHistory(data);
  }catch(e){errEl.textContent='Connection error.';errEl.style.display='block'}
  finally{btn.disabled=false;btn.textContent='Analyse thyroid function'}
}

// ── Show Result ──
function showResult(d){
  const sec=document.getElementById('results-section');sec.style.display='block';
  sec.classList.remove('fade-up');void sec.offsetWidth;sec.classList.add('fade-up');
  const icons={'Normal':'✅','Hypothyroidism':'⚠️','Hyperthyroidism':'🔴'};
  const cls={'Normal':'normal','Hypothyroidism':'hypo','Hyperthyroidism':'hyper'};
  const subs={'Normal':'Thyroid function within expected range','Hypothyroidism':'Underactive thyroid detected','Hyperthyroidism':'Overactive thyroid detected'};
  const c=cls[d.result];
  document.getElementById('result-icon').textContent=icons[d.result];
  document.getElementById('result-icon').className='result-icon '+c;
  document.getElementById('result-title').innerHTML=d.result+'<span class="severity-badge '+d.severity+'">'+d.severity+'</span>';
  document.getElementById('result-title').className='result-title '+c;
  document.getElementById('result-subtitle').textContent=subs[d.result];
  // Gauge
  drawGauge(d.risk_score,d.risk);
  // Comparison bars
  drawComparison(d);
  // Flags
  const fl=document.getElementById('flags-list');fl.innerHTML='';
  d.flags.forEach(f=>{
    const bad=f.includes('elevated')||f.includes('low')||f.includes('suppressed');
    fl.innerHTML+='<div class="flag-item"><div class="flag-dot '+(bad?(d.result==='Normal'?'warning':'danger'):'ok')+'"></div><span>'+f+'</span></div>';
  });
  // Tips
  const tl=document.getElementById('tips-list');tl.innerHTML='';
  d.tips.forEach((t,i)=>{tl.innerHTML+='<div class="tip-item"><div class="tip-num">'+(i+1)+'</div><span>'+t+'</span></div>'});
  // Explanation
  document.getElementById('explanation-text').textContent=d.explanation;
  // Logic
  const ll=document.getElementById('logic-list');ll.innerHTML='';
  d.logic.forEach(s=>{ll.innerHTML+='<div class="logic-step">'+s+'</div>'});
  // Confidence
  document.getElementById('confidence-text').textContent=d.confidence_explanation;
  // Causes
  const cl=document.getElementById('causes-list');cl.innerHTML='';
  if(d.possible_causes.length===0)cl.innerHTML='<div style="color:var(--text3);font-size:13px">No concerning causes — thyroid function is normal.</div>';
  else d.possible_causes.forEach(c=>{cl.innerHTML+='<div class="cause-item"><div class="cause-name">'+c.name+'</div><div class="cause-desc">'+c.desc+'</div></div>'});
  // Diet
  const dl=document.getElementById('diet-list');dl.innerHTML='';
  d.diet.forEach(x=>{dl.innerHTML+='<div class="rec-item"><div class="rec-icon">'+x.icon+'</div><div><div class="rec-title">'+x.item+'</div><div class="rec-detail">'+x.detail+'</div></div></div>'});
  // Lifestyle
  const ls=document.getElementById('lifestyle-list');ls.innerHTML='';
  d.lifestyle.forEach(x=>{ls.innerHTML+='<div class="rec-item"><div class="rec-icon">'+x.icon+'</div><div><div class="rec-title">'+x.tip+'</div><div class="rec-detail">'+x.detail+'</div></div></div>'});
  // Clinical
  const cv=document.getElementById('clinical-body');
  const r=d.ranges;
  cv.innerHTML='<div class="clinical-row"><span>TSH</span><span>'+d.values.tsh+' mIU/L (ref: '+r.tsh_low+'–'+r.tsh_high+')</span></div>'
    +'<div class="clinical-row"><span>T3</span><span>'+d.values.t3+' nmol/L (ref: '+r.t3_low+'–'+r.t3_high+')</span></div>'
    +'<div class="clinical-row"><span>T4</span><span>'+d.values.t4+' nmol/L (ref: '+r.t4_low+'–'+r.t4_high+')</span></div>'
    +'<div class="clinical-row"><span>Score</span><span>'+d.score+' (adj: '+d.adjusted_score+')</span></div>'
    +'<div class="clinical-row"><span>Classification</span><span>'+d.result+' — '+d.severity+'</span></div>'
    +'<div class="clinical-row"><span>Risk</span><span>'+d.risk+' ('+d.risk_score+'%)</span></div>';

  // Symptom Analysis
  const saCard=document.getElementById('symptom-analysis-card');
  const saList=document.getElementById('symptom-analysis-list');
  const saSummary=document.getElementById('symptom-summary');
  if(d.symptom_analysis && d.symptom_analysis.length>0){
    saCard.style.display='block';
    saSummary.textContent=d.symptom_summary||'';
    saList.innerHTML='';
    d.symptom_analysis.forEach(sa=>{
      const icon=sa.correlates?'✅':'❌';
      const statusClass=sa.correlates?'sa-supports':'sa-contradicts';
      const impactText=sa.score_impact!==0?(sa.score_impact>0?'+'+sa.score_impact:sa.score_impact)+' pts':'0 pts';
      saList.innerHTML+=
        '<div class="sa-item '+statusClass+'">'+
          '<div class="sa-header">'+
            '<span class="sa-icon">'+icon+'</span>'+
            '<span class="sa-name">'+sa.symptom+'</span>'+
            '<span class="sa-status-badge '+(sa.correlates?'sa-badge-yes':'sa-badge-no')+'">'+
              (sa.correlates?'Supports diagnosis':'Doesn\'t match pattern')+
            '</span>'+
            '<span class="sa-impact">'+(sa.score_impact!==0?impactText:'')+' </span>'+
          '</div>'+
          '<div class="sa-reason">'+sa.reason+'</div>'+
        '</div>';
    });
  }else{
    saCard.style.display='none';
  }

  // Alerts
  showAlerts(d);
  sec.scrollIntoView({behavior:'smooth',block:'start'});
}

// ── Gauge (SVG arc) ──
function drawGauge(val,risk){
  const colors={Low:'var(--success)',Medium:'var(--warning)',High:'var(--danger)'};
  const color=colors[risk]||'var(--accent)';
  const angle=val/100*180;
  const rad=n=>n*Math.PI/180;
  const cx=90,cy=95,r=70;
  const x1=cx+r*Math.cos(rad(180)),y1=cy+r*Math.sin(rad(180));
  const x2=cx+r*Math.cos(rad(180+angle)),y2=cy+r*Math.sin(rad(180+angle));
  const large=angle>180?1:0;
  document.getElementById('gauge-container').innerHTML=
    '<svg class="gauge-svg" viewBox="0 0 180 110">'
    +'<path d="M '+(cx-r)+' '+cy+' A '+r+' '+r+' 0 0 1 '+(cx+r)+' '+cy+'" fill="none" stroke="var(--glass-b)" stroke-width="12" stroke-linecap="round"/>'
    +'<path d="M '+x1+' '+y1+' A '+r+' '+r+' 0 '+large+' 1 '+x2+' '+y2+'" fill="none" stroke="'+color+'" stroke-width="12" stroke-linecap="round" style="filter:drop-shadow(0 0 6px '+color+')">'
    +'<animate attributeName="d" from="M '+x1+' '+y1+' A '+r+' '+r+' 0 0 1 '+x1+' '+y1+'" to="M '+x1+' '+y1+' A '+r+' '+r+' 0 '+large+' 1 '+x2+' '+y2+'" dur="1s" fill="freeze"/>'
    +'</path>'
    +'<text x="'+cx+'" y="'+(cy-15)+'" text-anchor="middle" fill="var(--text)" font-size="28" font-weight="700" font-family="Inter">'+val+'%</text>'
    +'<text x="'+cx+'" y="'+(cy+2)+'" text-anchor="middle" fill="var(--text3)" font-size="11" font-family="Inter">Risk Score</text>'
    +'</svg>';
}

// ── Comparison bars ──
function drawComparison(d){
  const box=document.getElementById('comparison-bars');box.innerHTML='';
  const items=[
    {name:'TSH',val:d.values.tsh,lo:d.ranges.tsh_low,hi:d.ranges.tsh_high,unit:'mIU/L',max:10},
    {name:'T3',val:d.values.t3,lo:d.ranges.t3_low,hi:d.ranges.t3_high,unit:'nmol/L',max:4},
    {name:'T4',val:d.values.t4,lo:d.ranges.t4_low,hi:d.ranges.t4_high,unit:'nmol/L',max:250}
  ];
  items.forEach(m=>{
    const pct=v=>Math.min(100,Math.max(0,(v/m.max)*100));
    const ok=m.val>=m.lo&&m.val<=m.hi;
    box.innerHTML+='<div class="comp-bar"><div class="label"><span>'+m.name+'</span><span style="color:var(--text3)">'+m.val+' '+m.unit+'</span></div>'
      +'<div class="bar-track"><div class="bar-normal" style="left:'+pct(m.lo)+'%;width:'+(pct(m.hi)-pct(m.lo))+'%"></div>'
      +'<div class="bar-marker '+(ok?'ok':'bad')+'" style="left:'+pct(m.val)+'%"></div></div>'
      +'<div class="val-label">Normal: '+m.lo+'–'+m.hi+' '+m.unit+'</div></div>';
  });
}

// ── Expand/collapse ──
function toggleExpand(id){
  const el=document.getElementById(id);el.classList.toggle('open');
  const btn=el.previousElementSibling;btn.querySelector('.arrow').textContent=el.classList.contains('open')?'▲':'▼';
}

// ── Doctor Mode ──
function toggleDoctor(){
  const btn=document.getElementById('doctor-btn');btn.classList.toggle('active');
  document.getElementById('clinical-body').classList.toggle('show');
}

// ── History ──
function saveHistory(d){
  history.unshift({date:new Date().toLocaleString(),tsh:d.values.tsh,t3:d.values.t3,t4:d.values.t4,result:d.result,severity:d.severity,risk_score:d.risk_score});
  if(history.length>20)history.pop();
  localStorage.setItem('thyro_history',JSON.stringify(history));
  renderHistory();updateTrendChart();
}
function renderHistory(){
  const tb=document.getElementById('history-body');
  if(!history.length){tb.innerHTML='<tr><td colspan="6" class="no-data">No test history yet. Run an analysis to start tracking.</td></tr>';return}
  tb.innerHTML='';
  history.forEach((h,i)=>{
    let trend='';
    if(i<history.length-1){
      const prev=history[i+1];
      const diff=h.risk_score-prev.risk_score;
      if(diff>5)trend='<span class="trend-badge up">↑ Rising</span>';
      else if(diff<-5)trend='<span class="trend-badge down">↓ Improving</span>';
      else trend='<span class="trend-badge stable">→ Stable</span>';
    }
    const cls={'Normal':'var(--success)','Hypothyroidism':'var(--warning)','Hyperthyroidism':'var(--danger)'};
    tb.innerHTML+='<tr><td>'+h.date+'</td><td>'+h.tsh+'</td><td>'+h.t3+'</td><td>'+h.t4+'</td><td style="color:'+cls[h.result]+'">'+h.result.replace('thyroidism','.')+'</td><td>'+trend+'</td></tr>';
  });
}
function clearHistory(){if(confirm('Clear all history?')){history=[];localStorage.removeItem('thyro_history');renderHistory();updateTrendChart()}}

// ── Trend Chart ──
function updateTrendChart(){
  const ctx=document.getElementById('trend-canvas');if(!ctx)return;
  const rev=[...history].reverse();
  const labels=rev.map(h=>h.date.split(',')[0]);
  const r=customRanges||DEFAULTS;
  if(trendChart)trendChart.destroy();
  const gridColor=getComputedStyle(document.documentElement).getPropertyValue('--glass-b').trim();
  const textColor=getComputedStyle(document.documentElement).getPropertyValue('--text3').trim();
  trendChart=new Chart(ctx,{type:'line',data:{labels,datasets:[
    {label:'TSH',data:rev.map(h=>h.tsh),borderColor:'#818cf8',backgroundColor:'rgba(129,140,248,.1)',tension:.3,fill:false,pointRadius:4},
    {label:'T3',data:rev.map(h=>h.t3),borderColor:'#34d399',backgroundColor:'rgba(52,211,153,.1)',tension:.3,fill:false,pointRadius:4},
    {label:'T4',data:rev.map(h=>h.t4),borderColor:'#fbbf24',backgroundColor:'rgba(251,191,36,.1)',tension:.3,fill:false,pointRadius:4,yAxisID:'y1'}
  ]},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
    plugins:{legend:{labels:{color:textColor,font:{family:'Inter',size:11}}}},
    scales:{y:{grid:{color:gridColor},ticks:{color:textColor,font:{size:10}},title:{display:true,text:'TSH / T3',color:textColor}},
      y1:{position:'right',grid:{drawOnChartArea:false},ticks:{color:textColor,font:{size:10}},title:{display:true,text:'T4',color:textColor}},
      x:{grid:{color:gridColor},ticks:{color:textColor,font:{size:10}}}}}});
}

// ── Smart Alerts ──
function showAlerts(d){
  const box=document.getElementById('alerts-box');box.innerHTML='';
  if(d.result==='Normal'){box.innerHTML='<div class="alert-item info"><span class="alert-icon">✅</span>All markers within normal range. Keep up the healthy lifestyle!</div>';return}
  if(d.severity==='Severe'){
    box.innerHTML+='<div class="alert-item critical"><span class="alert-icon">🚨</span><div><strong>Critical:</strong> Your values are severely abnormal. Consult a doctor within 24-48 hours.</div></div>';
  }else if(d.severity==='Moderate'){
    box.innerHTML+='<div class="alert-item warn"><span class="alert-icon">⚠️</span><div><strong>Attention:</strong> Moderate thyroid dysfunction detected. Schedule a doctor visit within 1-2 weeks.</div></div>';
  }else{
    box.innerHTML+='<div class="alert-item info"><span class="alert-icon">ℹ️</span><div>Mild deviation detected. Monitor and retest in 4-6 weeks.</div></div>';
  }
  if(d.values.tsh<0.1)box.innerHTML+='<div class="alert-item critical"><span class="alert-icon">🔴</span><div>TSH is critically low ('+d.values.tsh+' mIU/L). Risk of thyroid storm.</div></div>';
  if(d.values.tsh>10)box.innerHTML+='<div class="alert-item critical"><span class="alert-icon">🔴</span><div>TSH is critically high ('+d.values.tsh+' mIU/L). Severe hypothyroidism likely.</div></div>';
  if(history.length>=3){
    const recent=history.slice(0,3);
    const allAbnormal=recent.every(h=>h.result!=='Normal');
    if(allAbnormal)box.innerHTML+='<div class="alert-item warn"><span class="alert-icon">📊</span><div>Last 3 tests show persistent abnormal results. Consistent treatment needed.</div></div>';
  }
}

// ── Settings Modal ──
function openSettings(){document.getElementById('settings-modal').classList.add('show')}
function closeSettings(){document.getElementById('settings-modal').classList.remove('show')}
function saveSettings(){
  customRanges={
    tsh_low:+document.getElementById('r-tsh-low').value||DEFAULTS.tsh_low,
    tsh_high:+document.getElementById('r-tsh-high').value||DEFAULTS.tsh_high,
    t3_low:+document.getElementById('r-t3-low').value||DEFAULTS.t3_low,
    t3_high:+document.getElementById('r-t3-high').value||DEFAULTS.t3_high,
    t4_low:+document.getElementById('r-t4-low').value||DEFAULTS.t4_low,
    t4_high:+document.getElementById('r-t4-high').value||DEFAULTS.t4_high
  };
  localStorage.setItem('thyro_ranges',JSON.stringify(customRanges));
  closeSettings();colorInputs();
  // Update displayed ranges
  const r=customRanges;
  document.getElementById('tsh-range').textContent='Normal: '+r.tsh_low+'–'+r.tsh_high+' mIU/L';
  document.getElementById('t3-range').textContent='Normal: '+r.t3_low+'–'+r.t3_high+' nmol/L';
  document.getElementById('t4-range').textContent='Normal: '+r.t4_low+'–'+r.t4_high+' nmol/L';
}
function resetRanges(){customRanges=null;localStorage.removeItem('thyro_ranges');closeSettings();colorInputs();location.reload()}

// ── PDF (jsPDF direct text) ──
function downloadPDF(){
  if(!lastResult){alert('Run an analysis first.');return}
  const d=lastResult,v=d.values,r=d.ranges;
  const{jsPDF}=window.jspdf;
  const doc=new jsPDF({unit:'mm',format:'a4'});
  const W=210,M=15;let y=15;const pw=W-2*M;

  function addPage(){doc.addPage();y=15;}
  function checkPage(need){if(y+need>280)addPage();}
  function heading(text){
    checkPage(12);
    doc.setFontSize(13);doc.setFont('helvetica','bold');doc.setTextColor(124,58,237);
    doc.text(text,M,y);y+=2;
    doc.setDrawColor(226,232,240);doc.setLineWidth(0.5);doc.line(M,y,W-M,y);y+=6;
  }
  function bodyText(text,indent){
    doc.setFontSize(9);doc.setFont('helvetica','normal');doc.setTextColor(71,85,105);
    const lines=doc.splitTextToSize(text,pw-(indent||0));
    checkPage(lines.length*4+2);
    doc.text(lines,M+(indent||0),y);y+=lines.length*4+2;
  }

  // ─── HEADER ───
  doc.setFillColor(124,58,237);doc.rect(0,0,W,28,'F');
  doc.setFontSize(20);doc.setFont('helvetica','bold');doc.setTextColor(255,255,255);
  doc.text('ThyroCheck',M,14);
  doc.setFontSize(9);doc.setFont('helvetica','normal');
  doc.text('AI-Assisted Thyroid Screening Report',M,20);
  doc.setFontSize(8);doc.text('Date: '+new Date().toLocaleString(),W-M,14,{align:'right'});
  doc.text('ID: TC-'+Date.now().toString(36).toUpperCase(),W-M,19,{align:'right'});
  y=36;

  // ─── DIAGNOSIS BOX ───
  const sc=d.result==='Normal'?[22,163,74]:d.result==='Hypothyroidism'?[217,119,6]:[220,38,38];
  doc.setFillColor(sc[0],sc[1],sc[2]);doc.roundedRect(M,y,pw,22,3,3,'F');
  doc.setFontSize(16);doc.setFont('helvetica','bold');doc.setTextColor(255,255,255);
  doc.text(d.result,M+8,y+10);
  doc.setFontSize(10);doc.setFont('helvetica','normal');
  doc.text('Severity: '+d.severity+'  |  Risk: '+d.risk+' ('+d.risk_score+'%)',M+8,y+17);
  y+=30;

  // ─── LAB VALUES TABLE ───
  heading('Lab Values');
  doc.setFontSize(9);doc.setFont('helvetica','bold');doc.setTextColor(30,41,59);
  doc.text('Marker',M,y);doc.text('Your Value',M+50,y);doc.text('Normal Range',M+100,y);doc.text('Status',M+145,y);
  y+=2;doc.setDrawColor(226,232,240);doc.line(M,y,W-M,y);y+=5;
  doc.setFont('helvetica','normal');
  const markers=[
    {n:'TSH',val:v.tsh+' mIU/L',ref:r.tsh_low+'–'+r.tsh_high+' mIU/L',ok:v.tsh>=r.tsh_low&&v.tsh<=r.tsh_high},
    {n:'T3',val:v.t3+' nmol/L',ref:r.t3_low+'–'+r.t3_high+' nmol/L',ok:v.t3>=r.t3_low&&v.t3<=r.t3_high},
    {n:'T4',val:v.t4+' nmol/L',ref:r.t4_low+'–'+r.t4_high+' nmol/L',ok:v.t4>=r.t4_low&&v.t4<=r.t4_high}
  ];
  markers.forEach(m=>{
    doc.setTextColor(30,41,59);doc.text(m.n,M,y);doc.text(m.val,M+50,y);doc.text(m.ref,M+100,y);
    if(m.ok){doc.setTextColor(22,163,74);doc.text('Normal',M+145,y);}
    else{doc.setTextColor(220,38,38);doc.text('Abnormal',M+145,y);}
    y+=6;
  });
  y+=4;

  // ─── MARKER ANALYSIS ───
  heading('Marker Analysis');
  d.flags.forEach(f=>{
    const bad=f.includes('elevated')||f.includes('low')||f.includes('suppressed');
    if(bad){doc.setFillColor(220,38,38);}else{doc.setFillColor(22,163,74);}
    doc.circle(M+2,y-1.5,1.5,'F');
    doc.setTextColor(71,85,105);doc.setFontSize(9);doc.setFont('helvetica','normal');
    doc.text(f,M+7,y);y+=5;
  });
  y+=4;

  // ─── INTERPRETATION ───
  heading('Report Interpretation');
  bodyText(d.explanation);
  y+=2;

  // ─── CONFIDENCE ───
  doc.setFillColor(240,240,255);doc.roundedRect(M,y,pw,10,2,2,'F');
  doc.setDrawColor(124,58,237);doc.setLineWidth(0.8);doc.line(M,y,M,y+10);
  doc.setFontSize(9);doc.setFont('helvetica','bold');doc.setTextColor(124,58,237);
  doc.text('Confidence: ',M+4,y+6);
  doc.setFont('helvetica','normal');doc.setTextColor(71,85,105);
  const confLines=doc.splitTextToSize(d.confidence_explanation,pw-40);
  doc.text(confLines,M+30,y+6);
  y+=14;

  // ─── DIAGNOSTIC REASONING ───
  checkPage(40);
  heading('Diagnostic Reasoning');
  doc.setFont('courier','normal');doc.setFontSize(8);doc.setTextColor(71,85,105);
  d.logic.forEach(s=>{checkPage(5);doc.text('→ '+s,M,y);y+=4.5;});
  y+=4;

  // ─── SYMPTOM ANALYSIS ───
  if(d.symptom_analysis&&d.symptom_analysis.length>0){
    checkPage(20);
    heading('Symptom–Thyroid Correlation');
    if(d.symptom_summary){bodyText(d.symptom_summary);}
    d.symptom_analysis.forEach(sa=>{
      checkPage(16);
      const icon=sa.correlates?'✓':'✗';
      if(sa.correlates){doc.setTextColor(22,163,74);}else{doc.setTextColor(220,38,38);}
      doc.setFontSize(10);doc.setFont('helvetica','bold');
      doc.text(icon,M,y);
      doc.setTextColor(30,41,59);doc.setFontSize(9);
      doc.text(sa.symptom+' — '+(sa.correlates?'Supports diagnosis':'Does not match pattern'),M+6,y);
      y+=4;
      bodyText(sa.reason,6);
      y+=1;
    });
    y+=2;
  }

  // ─── POSSIBLE CAUSES ───
  if(d.possible_causes.length>0){
    checkPage(20);
    heading('Possible Causes');
    d.possible_causes.forEach(c=>{
      checkPage(10);
      doc.setFontSize(9);doc.setFont('helvetica','bold');doc.setTextColor(30,41,59);
      doc.text('• '+c.name,M,y);y+=4;
      bodyText(c.desc,4);
    });
    y+=2;
  }

  // ─── DIET ───
  checkPage(20);
  heading('Diet Recommendations');
  d.diet.forEach(x=>{
    checkPage(8);
    doc.setFontSize(9);doc.setFont('helvetica','bold');doc.setTextColor(30,41,59);
    doc.text(x.icon+' '+x.item,M,y);y+=4;
    bodyText(x.detail,4);
  });

  // ─── LIFESTYLE ───
  checkPage(20);
  heading('Lifestyle Suggestions');
  d.lifestyle.forEach(x=>{
    checkPage(8);
    doc.setFontSize(9);doc.setFont('helvetica','bold');doc.setTextColor(30,41,59);
    doc.text(x.icon+' '+x.tip,M,y);y+=4;
    bodyText(x.detail,4);
  });

  // ─── HEALTH GUIDANCE ───
  checkPage(20);
  heading('Health Guidance');
  d.tips.forEach((t,i)=>{checkPage(6);bodyText((i+1)+'. '+t);});

  // ─── FOOTER ───
  const pages=doc.getNumberOfPages();
  for(let i=1;i<=pages;i++){
    doc.setPage(i);
    doc.setFontSize(7);doc.setFont('helvetica','normal');doc.setTextColor(148,163,184);
    doc.text('ThyroCheck AI Screening Report — For educational purposes only. Not a substitute for medical diagnosis.',W/2,290,{align:'center'});
    doc.text('Page '+i+' of '+pages,W-M,290,{align:'right'});
  }

  doc.save('ThyroCheck_Report_'+new Date().toISOString().slice(0,10)+'.pdf');
}

// ── Init ──
document.addEventListener('DOMContentLoaded',()=>{
  document.getElementById('theme-btn').textContent=document.documentElement.dataset.theme==='dark'?'☀️ Light':'🌙 Dark';
  renderHistory();
  if(history.length)updateTrendChart();
  // Load custom ranges into settings
  const r=customRanges||DEFAULTS;
  document.getElementById('r-tsh-low').value=r.tsh_low;document.getElementById('r-tsh-high').value=r.tsh_high;
  document.getElementById('r-t3-low').value=r.t3_low;document.getElementById('r-t3-high').value=r.t3_high;
  document.getElementById('r-t4-low').value=r.t4_low;document.getElementById('r-t4-high').value=r.t4_high;
});
