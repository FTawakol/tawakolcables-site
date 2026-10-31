/* Altawakol Cables — client scripts (no dependencies) */
(function(){
  var H = document.documentElement, ROOT = H.getAttribute('data-root') || '', LANG = H.lang || 'en';
  var T = window.ATC_T || {};
  function t(k){ return T[k] || k; }
  function qs(s,el){ return (el||document).querySelector(s); }
  function qsa(s,el){ return Array.prototype.slice.call((el||document).querySelectorAll(s)); }
  function langPath(p){ return ROOT + (LANG==='ar' ? '/ar' : '') + p; }

  /* mobile menu */
  var mb = qs('.menu-btn'); if(mb){ mb.addEventListener('click', function(){ var n=qs('.nav'); var o=n.classList.toggle('open'); mb.setAttribute('aria-expanded', o?'true':'false'); }); }

  /* compare selection stored per browser */
  var CMP_KEY='atc_compare';
  function cmpGet(){ try{ return JSON.parse(localStorage.getItem(CMP_KEY)||'[]'); }catch(e){ return []; } }
  function cmpSet(a){ try{ localStorage.setItem(CMP_KEY, JSON.stringify(a.slice(0,4))); }catch(e){} renderCmpBar(); }
  function cmpToggle(code){ var a=cmpGet(); var i=a.indexOf(code); if(i>=0) a.splice(i,1); else { if(a.length>=4) a.shift(); a.push(code);} cmpSet(a); return a.indexOf(code)>=0; }
  function renderCmpBar(){
    var bar=qs('.compare-bar'); if(!bar) return; var a=cmpGet();
    bar.classList.toggle('show', a.length>0);
    var list=qs('.compare-bar .list'); if(list) list.textContent=a.join(', ');
    var go=qs('.compare-bar .go'); if(go){ go.href=langPath('/tools/compare/')+'?codes='+a.join(','); go.classList.toggle('btn-primary', a.length>=2); }
    qsa('input[data-cmp]').forEach(function(cb){ cb.checked = a.indexOf(cb.getAttribute('data-cmp'))>=0; });
    qsa('[data-cmp-add]').forEach(function(b){ var c=b.getAttribute('data-cmp-add'); b.setAttribute('aria-pressed', a.indexOf(c)>=0?'true':'false'); b.textContent = a.indexOf(c)>=0 ? (t('added_compare')||'In compare list') : (t('add_compare')||'Add to compare'); });
  }
  document.addEventListener('change', function(e){ var cb=e.target; if(cb.matches && cb.matches('input[data-cmp]')){ cmpToggle(cb.getAttribute('data-cmp')); } });
  document.addEventListener('click', function(e){ var b=e.target.closest && e.target.closest('[data-cmp-add]'); if(b){ e.preventDefault(); cmpToggle(b.getAttribute('data-cmp-add')); } var cl=e.target.closest && e.target.closest('.compare-bar .clear'); if(cl){ e.preventDefault(); cmpSet([]); } });
  renderCmpBar();

  /* table filter */
  var tbl=qs('table.data[data-filter]');
  if(tbl){
    var rows=qsa('tbody tr', tbl), fs=qs('.filters');
    function apply(){
      var series=(qs('[name=series]',fs)||{}).value||'all', mn=parseFloat((qs('[name=min]',fs)||{}).value)||0, mx=parseFloat((qs('[name=max]',fs)||{}).value)||1e9, q=((qs('[name=q]',fs)||{}).value||'').toLowerCase().trim();
      var n=0; rows.forEach(function(r){ var ok=true; var s=r.getAttribute('data-series'); var a=parseFloat(r.getAttribute('data-area'));
        if(series!=='all' && s!==series) ok=false; if(a<mn||a>mx) ok=false; if(q && r.textContent.toLowerCase().indexOf(q)<0) ok=false;
        r.style.display=ok?'':'none'; if(ok) n++; });
      var c=qs('.filters .count'); if(c) c.textContent=t('showing')+' '+n+' '+t('of')+' '+rows.length;
    }
    qsa('input,select',fs).forEach(function(i){ i.addEventListener('input',apply); });
    var rs=qs('.filters .reset'); if(rs) rs.addEventListener('click',function(){ qsa('input',fs).forEach(function(i){i.value='';}); var s=qs('[name=series]',fs); if(s) s.value='all'; apply(); });
    apply();
  }

  /* data loader */
  var DATA=null; function loadData(cb){ if(DATA) return cb(DATA); fetch(ROOT+'/data/conductors.json').then(function(r){return r.json();}).then(function(d){ DATA=d; cb(d); }); }
  function codeUrl(c){ return langPath('/products/'+c.product_code.toLowerCase()+'/'); }
  function label(c){ return c.family+' '+(c.code_name? c.code_name+' ('+c.designation_or_area+')' : c.designation_or_area)+' · '+c.product_code; }

  /* selector */
  var sel=qs('#selector');
  if(sel){
    sel.addEventListener('submit', function(e){ e.preventDefault(); var f=sel;
      var fam=f.family.value, env=f.env.value, cur=parseFloat(f.current.value), area=parseFloat(f.area.value), series=f.series.value;
      loadData(function(d){
        var out=qs('#sel-results'); out.innerHTML='';
        var list=d.filter(function(c){ return (fam==='any'||c.family===fam) && (series==='all'||c.series===series); });
        if(fam==='any'){ if(env==='coastal') list=list.filter(function(c){return c.family==='AAAC';}); if(env==='span') list=list.filter(function(c){return c.family==='ACSR';}); }
        list=list.filter(function(c){ if(cur) return c.current_rating_A>=cur; if(area) return c.area_al_mm2>=area*0.9; return true; });
        list.sort(function(a,b){ return cur ? a.current_rating_A-b.current_rating_A : a.area_al_mm2-b.area_al_mm2; });
        var picks=list.slice(0,3);
        if(!picks.length){ out.innerHTML='<p class="muted">'+t('sel_none')+'</p>'; return; }
        picks.forEach(function(c,i){ var el=document.createElement('div'); el.className='sel-card'+(i===0?' best':'');
          el.innerHTML='<div><div class="t"><a href="'+codeUrl(c)+'">'+label(c)+'</a></div><div class="d">'+c.area_al_mm2+' '+t('u_mm2')+' Al · <b>'+c.current_rating_A+' '+t('u_a')+'</b> · '+c.overall_diameter_mm+' '+t('u_mm')+' · '+c.mass_kg_km+' '+t('u_kgkm')+' · RTS <b>'+c.rts_kN+' '+t('u_kn')+'</b></div></div>'
            +'<div><a class="btn btn-sm btn-ghost" href="'+codeUrl(c)+'">'+(t('specification'))+'</a> <a class="btn btn-sm btn-primary" href="'+langPath('/contact/')+'?code='+encodeURIComponent(c.product_code)+'">'+t('hero_cta2')+'</a></div>';
          out.appendChild(el); });
      });
    });
  }

  /* compare page */
  var cmp=qs('#compare');
  if(cmp){
    var params=new URLSearchParams(location.search); var codes=(params.get('codes')||'').split(',').filter(Boolean); if(!codes.length) codes=cmpGet();
    loadData(function(d){
      var byCode={}; d.forEach(function(c){ byCode[c.product_code]=c; byCode[c.product_code.toLowerCase()]=c; if(c.code_name) byCode[c.code_name.toLowerCase()]=c; });
      var dl=qs('#cmp-list'); if(dl){ d.forEach(function(c){ var o=document.createElement('option'); o.value=c.product_code; o.label=label(c); dl.appendChild(o); }); }
      var add=qs('#cmp-add'); if(add){ add.addEventListener('submit',function(e){ e.preventDefault(); var v=add.code.value.trim().toLowerCase(); var c=byCode[v]; if(c){ var a=cmpGet(); if(a.indexOf(c.product_code)<0){ if(a.length>=4) a.shift(); a.push(c.product_code); cmpSet(a);} codes=cmpGet(); render(); add.code.value=''; } }); }
      function render(){
        var sel=codes.map(function(k){return byCode[k]||byCode[k.toLowerCase()];}).filter(Boolean);
        var host=qs('#cmp-table'); if(!sel.length){ host.innerHTML='<p class="muted">'+t('compare_empty')+'</p>'; return; }
        var fields=[['family',null,'th_family'],['series',null,'filter_series'],['code_name',null,'th_name'],['designation_or_area',null,'th_designation'],['area_al_mm2','u_mm2','th_area_al'],['area_steel_mm2','u_mm2','th_area_st'],['total_area_mm2','u_mm2','th_area_total'],['stranding_al','u_nomm','th_stranding_al'],['stranding_steel','u_nomm','th_stranding_st'],['overall_diameter_mm','u_mm','th_diameter'],['mass_kg_km','u_kgkm','th_mass'],['dc_resistance_20C_ohm_km','u_ohmkm','th_resistance'],['rts_kN','u_kn','th_rts'],['current_rating_A','u_a','th_current']];
        var h='<div class="tablewrap"><table class="data cmp"><thead><tr><th></th>'+sel.map(function(c){return '<th class="n"><a href="'+codeUrl(c)+'" style="color:#fff">'+c.product_code+'</a><span class="u">'+c.family+' '+(c.code_name||c.designation_or_area)+'</span></th>';}).join('')+'</tr></thead><tbody>';
        fields.forEach(function(f){ var vals=sel.map(function(c){return c[f[0]];}); var nums=vals.map(parseFloat).filter(function(x){return !isNaN(x);}); var mn=Math.min.apply(null,nums), mx=Math.max.apply(null,nums); var spread=nums.length>1 && mn>0 && (mx-mn)/mn>0.10;
          h+='<tr><th class="hd">'+t(f[2])+(f[1]?' <span class="u" style="color:#5B6478">'+t(f[1])+'</span>':'')+'</th>'+vals.map(function(v){ var n=parseFloat(v); var cls='n'+((spread&&!isNaN(n)&&(n===mn||n===mx))?' diff':''); return '<td class="'+cls+'">'+(v===''||v==null?'—':v)+'</td>'; }).join('')+'</tr>'; });
        h+='<tr><th class="hd"></th>'+sel.map(function(c){return '<td class="n"><a class="small" href="#" data-rm="'+c.product_code+'">'+t('compare_remove')+'</a></td>';}).join('')+'</tr></tbody></table></div>';
        host.innerHTML=h;
        qsa('[data-rm]',host).forEach(function(a){ a.addEventListener('click',function(e){ e.preventDefault(); var k=a.getAttribute('data-rm'); var arr=cmpGet().filter(function(x){return x!==k;}); cmpSet(arr); codes=codes.filter(function(x){return x.toLowerCase()!==k.toLowerCase();}); render(); }); });
      }
      render();
    });
  }

  /* RFQ form: posts to data-endpoint (Formspree/Web3Forms) when set; otherwise opens the visitor's email app prefilled */
  var rfq=qs('#rfq');
  if(rfq){
    var p=new URLSearchParams(location.search); if(p.get('code')&&rfq.code) rfq.code.value=p.get('code');
    function refNo(){ var d=new Date(); return 'ATC-RFQ-'+d.getFullYear()+('0'+(d.getMonth()+1)).slice(-2)+('0'+d.getDate()).slice(-2)+'-'+Math.random().toString(16).slice(2,6).toUpperCase(); }
    function bodyText(ref){ return qsa('input,select,textarea',rfq).filter(function(i){return i.name && i.name!=='website';}).map(function(i){return i.name+': '+i.value;}).concat(['reference: '+ref,'page: '+location.href,'language: '+LANG]).join('\n'); }
    rfq.addEventListener('submit',function(e){ e.preventDefault();
      if(!rfq.reportValidity()) return;
      var btn=qs('button[type=submit]',rfq); var okm=qs('.msg.ok-box',rfq.parentNode), erm=qs('.msg.err-box',rfq.parentNode); okm.className='msg ok-box'; erm.className='msg err-box';
      var mail=rfq.getAttribute('data-mail')||'', ep=rfq.getAttribute('data-endpoint')||'', ref=refNo();
      var subject='RFQ '+ref+': '+(rfq.code.value||'')+(rfq.company.value?' ('+rfq.company.value+')':'');
      if(!ep){ location.href='mailto:'+mail+'?subject='+encodeURIComponent(subject)+'&body='+encodeURIComponent(bodyText(ref)); okm.innerHTML='<b>'+t('f_ok')+' '+ref+'.</b> '+t('f_mailto'); okm.className='msg ok ok-box'; return; }
      btn.disabled=true; var old=btn.textContent; btn.textContent=t('f_sending');
      var fd=new FormData(rfq); fd.append('_subject',subject); fd.append('subject',subject); fd.append('reference',ref); fd.append('lang',LANG); fd.append('page',location.href);
      fetch(ep,{method:'POST',body:fd,headers:{'Accept':'application/json'}}).then(function(r){ if(!r.ok) throw new Error(r.status); okm.innerHTML='<b>'+t('f_ok')+' '+ref+'.</b> '+t('f_ok2'); okm.className='msg ok ok-box'; rfq.reset(); })
      .catch(function(){ erm.innerHTML=t('f_err')+' <a href="mailto:'+mail+'?subject='+encodeURIComponent(subject)+'&body='+encodeURIComponent(bodyText(ref))+'">'+mail+'</a>'; erm.className='msg err err-box'; })
      .then(function(){ btn.disabled=false; btn.textContent=old; });
    });
  }
})();
