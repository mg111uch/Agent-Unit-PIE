let store = { ingredients: {}, fridgeChoices: {}, freshMap: {} };
let currentRecipe = null;
let swapSource = null;
let dragKey = null;
let SLOTS = [];

function buildSlots(){
  SLOTS=[];
  MENU.forEach(m=>{
    ['brunch','lunch','dinner'].forEach(meal=>{
      SLOTS.push({key:`${m.id}_${meal}`, dayId:m.id, meal, dow:m.day});
    });
  });
}
function defaultFreshMap(){
  const mp={};
  MENU.forEach(m=>{
    mp[`${m.id}_brunch`]=m.brunch;
    mp[`${m.id}_lunch`]=m.lunch;
    mp[`${m.id}_dinner`]=m.dinner;
  });
  return mp;
}
async function loadStore(){
  try{ const r=await fetch('store.json'); if(r.ok) store=await r.json(); }catch(e){}
  buildSlots();
  if(!store.ingredients) store.ingredients={};
  if(!store.fridgeChoices) store.fridgeChoices={};
  if(!store.freshMap || Object.keys(store.freshMap).length===0) store.freshMap=defaultFreshMap();
  // ensure freshMap has all keys (if MENU changed)
  const def=defaultFreshMap();
  SLOTS.forEach(s=>{ if(!(s.key in store.freshMap)) store.freshMap[s.key]=def[s.key]; });
  // ensure ingredients for every recipe name present in freshMap values + original
  const allRecipes=new Set(Object.values(store.freshMap));
  MENU.forEach(m=> [m.brunch,m.lunch,m.dinner].forEach(r=>allRecipes.add(r)));
  allRecipes.forEach(r=>{ if(!(r in store.ingredients)) store.ingredients[r]=[]; });
}
function posOf(key){ return SLOTS.findIndex(s=>s.key===key); }
function optionsFor(key){
  const pos=posOf(key);
  const n=SLOTS.length;
  const out=[];
  for(let i=5;i>=1;i--){
    const p=(pos - i + n) % n;
    out.push(store.freshMap[SLOTS[p].key]);
  }
  return out;
}

function render(){
  const tbody=document.getElementById('tbody');
  tbody.innerHTML='';
  MENU.forEach((row,idx)=>{
    const tr=document.createElement('tr');
    const tdDay=document.createElement('td');
    tdDay.className='day';
    tdDay.innerHTML=`<div class="num">#${row.id}</div><div class="dow">${row.day}</div>`;
    tr.appendChild(tdDay);
    ['brunch','lunch','dinner'].forEach(meal=>{
      const key=`${row.id}_${meal}`;
      const td=document.createElement('td');
      const cell=document.createElement('div');
      cell.className='cell';
      const freshRec=store.freshMap[key];
      const tags=store.ingredients[freshRec]||[];
      const fresh=document.createElement('div');
      fresh.className='slot fresh';
      fresh.draggable=true;
      fresh.dataset.key=key;
      fresh.innerHTML=`<span class="badge">FRESH</span><div class="recipe" data-recipe="${esc(freshRec)}">${esc(freshRec)}</div><div class="tags">${tags.length?tags.map(t=>`<span class="tag">${esc(t)}</span>`).join(''):'<span class="tag muted">no tags — click recipe</span>'}</div><div class="fresh-foot"><span class="meta">${tags.length} tag(s)</span><button class="swap-btn" data-key="${key}">⇄ swap</button></div>`;
      // fridge - cyclic last 5 (Day1 uses tail of cycle = Day15 cycle)
      const fridge=document.createElement('div');
      const opts=optionsFor(key);
      fridge.className='slot fridge';
      let chosen=store.fridgeChoices[key];
      if(!chosen || !opts.includes(chosen)) { chosen=opts[opts.length-1]||opts[0]; store.fridgeChoices[key]=chosen; }
      const fTags=store.ingredients[chosen]||[];
      const uniq=[...new Set(opts)];
      fridge.innerHTML=`<span class="badge">FRIDGE · last 5 cyclic</span><select class="select" data-key="${key}">${uniq.map(o=>`<option value="${esc(o)}" ${o===chosen?'selected':''}>${esc(o)}</option>`).join('')}</select><div class="recipe" data-recipe="${esc(chosen)}">${esc(chosen)}</div><div class="tags">${fTags.length?fTags.map(t=>`<span class="tag">${esc(t)}</span>`).join(''):'<span class="tag muted">no tags</span>'}</div>`;
      cell.appendChild(fresh);
      cell.appendChild(fridge);
      td.appendChild(cell);
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  document.getElementById('countInfo').textContent=`· ${Object.keys(store.ingredients).length} recipes · ${countTags()} tags`;
  document.getElementById('notes').textContent=EXTRA_NOTES.join(' · ');
  bindEvents();
}
function esc(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function countTags(){return Object.values(store.ingredients).reduce((a,b)=>a+b.length,0);}
let saveTimer=null;
function scheduleSave(){
  clearTimeout(saveTimer);
  saveTimer=setTimeout(async()=>{
    try{
      const r=await fetch("api/save",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(store)});
      if(r.ok) document.getElementById("countInfo").title="autosaved";
    }catch(e){}
  },250);
}

function bindEvents(){
  document.querySelectorAll('.recipe').forEach(el=> el.onclick=()=> openDialog(el.dataset.recipe));
  document.querySelectorAll('.select').forEach(sel=> sel.onchange=e=>{
    store.fridgeChoices[e.target.dataset.key]=e.target.value;
    render(); scheduleSave();
  });
  document.querySelectorAll('.swap-btn').forEach(b=> b.onclick=e=>{
    e.stopPropagation();
    openSwap(b.dataset.key);
  });
  // drag swap
  document.querySelectorAll('.slot.fresh').forEach(el=>{
    el.ondragstart=e=>{ dragKey=el.dataset.key; el.classList.add('dragging'); e.dataTransfer.effectAllowed='move'; };
    el.ondragend=e=>{ el.classList.remove('dragging'); dragKey=null; document.querySelectorAll('.drop-hover').forEach(x=>x.classList.remove('drop-hover')); };
    el.ondragover=e=>{ e.preventDefault(); if(dragKey && dragKey!==el.dataset.key) el.classList.add('drop-hover'); };
    el.ondragleave=e=> el.classList.remove('drop-hover');
    el.ondrop=e=>{
      e.preventDefault(); el.classList.remove('drop-hover');
      const target=el.dataset.key;
      if(dragKey && target && dragKey!==target) doSwap(dragKey,target);
    };
  });
}
function openDialog(recipe){
  currentRecipe=recipe;
  document.getElementById('dlgTitle').textContent=recipe+' — ingredients';
  renderChips();
  document.getElementById('dlg').showModal();
  document.getElementById('tagInput').focus();
}
function renderChips(){
  const c=document.getElementById('chips');
  const tags=store.ingredients[currentRecipe]||[];
  c.innerHTML=tags.length?tags.map((t,i)=>`<span class="chip">${esc(t)} <button data-i="${i}">×</button></span>`).join(''):'<span class="sub">No tags yet</span>';
  c.querySelectorAll('button').forEach(b=> b.onclick=()=>{
    store.ingredients[currentRecipe].splice(parseInt(b.dataset.i),1);
    renderChips(); render(); scheduleSave();
  });
}
function addTag(){
  const inp=document.getElementById('tagInput');
  const v=inp.value.trim();
  if(!v) return;
  if(!store.ingredients[currentRecipe]) store.ingredients[currentRecipe]=[];
  store.ingredients[currentRecipe].push(v);
  inp.value=''; renderChips(); render(); scheduleSave();
}
function openSwap(key){
  swapSource=key;
  const sel=document.getElementById('swapSelect');
  sel.innerHTML=SLOTS.filter(s=>s.key!==key).map(s=>{
    const rec=store.freshMap[s.key];
    return `<option value="${s.key}">#${s.dayId} ${s.dow} ${s.meal} — ${esc(rec)}</option>`;
  }).join('');
  const srcRec=store.freshMap[key];
  const srcSlot=SLOTS.find(s=>s.key===key);
  document.getElementById('swapInfo').textContent=`Swap "${srcRec}" at #${srcSlot.dayId} ${srcSlot.dow} ${srcSlot.meal} with:`;
  document.getElementById('swapDlg').showModal();
}
function doSwap(a,b){
  const tmp=store.freshMap[a];
  store.freshMap[a]=store.freshMap[b];
  store.freshMap[b]=tmp;
  render(); scheduleSave();
}
function downloadStore(){
  const blob=new Blob([JSON.stringify(store,null,2)],{type:'application/json'});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob); a.download='store.json'; a.click(); URL.revokeObjectURL(a.href);
}
function handleImport(e){
  const f=e.target.files[0]; if(!f) return;
  const rd=new FileReader();
  rd.onload=()=>{
    try{
      const j=JSON.parse(rd.result);
      if(j.ingredients) store.ingredients=j.ingredients;
      if(j.fridgeChoices) store.fridgeChoices=j.fridgeChoices;
      if(j.freshMap) store.freshMap=j.freshMap;
      if(!j.ingredients && !j.freshMap && typeof j==='object'){
        // flat ingredients map
        store.ingredients=j;
      }
      buildSlots();
      const def=defaultFreshMap();
      SLOTS.forEach(s=>{ if(!(s.key in store.freshMap)) store.freshMap[s.key]=def[s.key]; });
      render(); scheduleSave(); alert('Imported');
    }catch(err){ alert('Invalid JSON '+err.message); }
  };
  rd.readAsText(f); e.target.value='';
}
document.getElementById('addTag').onclick=addTag;
document.getElementById('tagInput').onkeydown=e=>{ if(e.key==='Enter') addTag(); };
document.getElementById('closeDlg').onclick=()=>document.getElementById('dlg').close();
document.getElementById('doneDlg').onclick=()=>document.getElementById('dlg').close();
document.getElementById('closeSwap').onclick=()=>document.getElementById('swapDlg').close();
document.getElementById('doSwap').onclick=()=>{
  const t=document.getElementById('swapSelect').value;
  if(swapSource && t) doSwap(swapSource,t);
  document.getElementById('swapDlg').close();
};
document.getElementById('saveBtn').onclick=downloadStore;
document.getElementById('importFile').onchange=handleImport;
document.getElementById('printBtn').onclick=()=>window.print();
document.getElementById('resetBtn').onclick=()=>{
  if(confirm('Reset swaps & fridge choices? Ingredients kept.')){
    store.freshMap=defaultFreshMap(); store.fridgeChoices={}; render(); scheduleSave();
  }
};
buildSlots();
loadStore().then(render);
