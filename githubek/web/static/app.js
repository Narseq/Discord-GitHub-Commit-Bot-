document.querySelectorAll('.chips').forEach(box=>{
  const hidden=box.querySelector('input[type=hidden]'),list=box.querySelector('.chiplist'),inp=box.querySelector('.chipadd');
  const sync=()=>{hidden.value=[...list.children].map(c=>c.dataset.id).join(',')};
  const add=v=>{
    const m=v.match(/\d{15,20}/); if(!m) return false;
    const id=m[0]; if([...list.children].some(c=>c.dataset.id===id)) return true;
    let label=id; if(inp.list){const o=[...inp.list.options].find(o=>o.value===id); if(o&&o.label) label=o.label;}
    const s=document.createElement('span'); s.className='chip'; s.dataset.id=id;
    s.append(label); if(label!==id){const t=document.createElement('small');t.textContent=id;s.append(t);}
    const x=document.createElement('b'); x.textContent='\u00d7'; s.append(x);
    list.append(s); sync(); return true;
  };
  const take=()=>{if(inp.value.trim()&&add(inp.value)) inp.value='';};
  inp.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===','){e.preventDefault();take();}});
  inp.addEventListener('change',take); inp.addEventListener('blur',take);
  list.addEventListener('click',e=>{if(e.target.tagName==='B'){e.target.parentElement.remove();sync();}});
});
