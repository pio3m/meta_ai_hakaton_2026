(() => {
  const jury=location.pathname.replace(/\/$/,'')==='/admin/jury';
  const base=jury?'/admin/jury/api':'/admin/api';
  const $=id=>document.getElementById(id);
  let logged=false, selected=null, busy=false, epoch=0;
  $('scope').textContent=jury?'Jury / tylko sesja demo':'Właściciel';
  $('owner-controls').hidden=jury;
  $('asset-controls').hidden=jury;
  $('jury-notice').hidden=!jury;
  $('prompt-section').hidden=jury;
  if(jury)$('login-help').textContent='Wklej token jury wygenerowany przez właściciela. Nie używaj tokenu ADMIN_TOKEN.';
  async function api(path,options={}){
    const response=await fetch(base+path,{credentials:'same-origin',cache:'no-store',...options,headers:{'Content-Type':'application/json',...(options.headers||{})}});
    const body=await response.json();
    if(!response.ok){const error=new Error(typeof body.detail==='string'?body.detail:'Błąd żądania.');error.status=response.status;throw error;}
    return body;
  }
  function lock(message=''){
    epoch++;logged=false;selected=null;$('login').hidden=false;$('dashboard').hidden=true;
    $('call-list').replaceChildren();$('detail').hidden=true;
    for(const id of ['prompt','reply','message','context','error','facts','director-json','validation','execution','guard','delivered-reply'])$(id).replaceChildren();
    $('npc-roster').replaceChildren();$('world-state').textContent='';$('world-location').textContent='Świat na żywo';
    $('jury-token').value='';$('demo-access').hidden=true;$('login-error').textContent=message;
  }
  function renderNpcs(world,languages={}){
    const t=window.chessCorpT??(x=>x);
    function prose(text){const tail=text.includes(': ')?text.split(': ').slice(1).join(': '):text;const source=languages[text]??languages[tail];if(source)return window.chessCorpOriginal(text,source);const engine=/^(Gracz (odwiedził:|rozmawia z|w pobliżu)|Lokalny start:|[A-Za-z_]+ (MOVE_TO|PATROL|WAIT|TALK_TO|INSPECT_TERMINAL|REACT_TO_PLAYER) \/ (completed|expired))/.test(text);return window.chessCorpIsAuthored(text)||window.chessCorpIsAuthored(tail)||engine?t(text):window.chessCorpOriginal(text,'und');}
    const roster=$('npc-roster');roster.replaceChildren();
    const states={MOVE_TO:'W drodze',PATROL:'Patroluje',WAIT:'Obserwuje',TALK_TO:'Rozmawia',INSPECT_TERMINAL:'Bada terminal',REACT_TO_PLAYER:'Reaguje na gracza'};
    if(!world?.npcs?.length){roster.textContent='Uruchom grę, aby zobaczyć NPC aktywnej sesji.';return;}
    for(const npc of world.npcs){
      const card=document.createElement('article');card.className='npc-card';
      const title=document.createElement('h3');title.textContent=npc.npc_id;
      const state=document.createElement('p');state.className='npc-state';state.textContent=(states[npc.state]??npc.state)+' · '+npc.source;
      const goal=document.createElement('p');goal.dataset.preserveOriginal='';goal.textContent=t('Cel')+': '+prose(npc.goal);
      const moods={calm:'spokojny',alert:'czujny',curious:'ciekawy',ambitious:'ambitny',suspicious:'podejrzliwy'};
      const meta=document.createElement('small');meta.textContent='Nastrój: '+(moods[npc.mood]??npc.mood)+' · Pozycja: '+npc.position.join(', ');
      const memory=document.createElement('p');memory.className='npc-memory';memory.dataset.preserveOriginal='';memory.textContent=(npc.memory??[]).slice(-2).map(prose).join(' / ');
      card.append(title,state,goal,meta,memory);roster.append(card);
    }
    const events=$('world-events');events.replaceChildren();for(const text of (world.events??[]).slice(-4)){const item=document.createElement('p');item.dataset.preserveOriginal='';item.textContent=prose(text);events.append(item);}
  }
  function tokenText(usage){return usage?`${usage.prompt_tokens??'?'} wej. / ${usage.completion_tokens??'?'} wyj. / ${usage.total_tokens??'?'} razem`:'brak danych';}
  function show(row){
    $('detail').hidden=false;$('selection-help').hidden=true;
    const fields={Typ:row.kind==='asset'?'Asset Generator':row.kind==='world'?'World AI':row.kind==='director'?'Game Director':'Czat NPC',Czas:new Date(row.started_at).toLocaleString(window.chessCorpGetLanguage()==='en'?'en-GB':'pl-PL'),Stan:row.state,Dostawca:row.provider,Model:row.model,'Czas wykonania':row.elapsed_ms===null?'w toku':`${row.elapsed_ms} ms`,Tokeny:tokenText(row.usage),'Status HTTP Meta':row.upstream_status??'—'};
    $('asset-section').hidden=row.kind!=='asset';
    $('asset-info').textContent=JSON.stringify(row.asset??{},null,2);
    if(row.kind==='asset'&&['hacker_emblem','cyber_rat','merchant'].includes(row.asset?.id))$('asset-preview').src='/api/assets/'+encodeURIComponent(row.asset.id)+'.png';
    else $('asset-preview').removeAttribute('src');
    if(row.context?.location_id)fields.Lokacja=row.context.location_id;
    if(row.kind==='world'){fields['Źródło planu']=row.plan_source??'oczekiwanie';fields.Limity=JSON.stringify(row.world_limits??{});}
    if(row.kind==='buddy')fields.Guard=row.guard_status??'oczekiwanie';
    if(row.kind==='director')fields['Typ questu']=row.quest_type??'oczekiwanie';
    if(!jury)fields.Sesja=row.session_id;
    $('facts').replaceChildren();
    for(const [key,value] of Object.entries(fields)){
      const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=key;dd.textContent=value;$('facts').append(dt,dd);
    }
    $('guard-section').hidden=row.kind!=='buddy';
    $('guard').textContent=JSON.stringify(row.guard,null,2);
    $('delivered-reply').textContent=row.delivered_reply?window.chessCorpOriginal(row.delivered_reply,row.language):window.chessCorpT('Oczekiwanie');
    $('director-section').hidden=!['director','world'].includes(row.kind);
    $('director-json').textContent=JSON.stringify(jury?row.validated_plan:(row.response_json??row.fallback_plan),null,2);
    $('execution').textContent=JSON.stringify(row.execution,null,2);
    $('validation').textContent=JSON.stringify(row.validation,null,2);
    $('context').textContent=JSON.stringify(row.context,null,2);
    $('message').textContent=row.message;
    $('reply').textContent=row.reply?window.chessCorpOriginal(row.reply,row.language):(row.state==='pending'?'Buddy pisze…':'Brak odpowiedzi');
    if(row.reply_truncated)$('reply').textContent+='\n[Podgląd ucięty do 16000 znaków]';
    $('error').textContent=window.chessCorpT(row.error||'Brak');
    if(!jury){
      $('sent-note').textContent=row.sent_to_model?'Payload z miejsca wykonania HTTP; sekrety są maskowane.':row.provider==='cache'?'Asset z cache. Poniżej oryginalny payload historycznej generacji; teraz nie wywołano modelu.':row.provider==='guard'?'Guard odpowiedział lokalnie. Brak wywołania LLM.':row.provider==='mock'?'Symulacja mock. Ten prompt NIE został wysłany do modelu.':'Żądanie nie zostało wysłane do modelu.';
      $('prompt').textContent=row.request_payload?JSON.stringify(row.request_payload,null,2):window.chessCorpT('Brak wysłanego payloadu.');
    }
  }
  async function refresh(){
    if(busy)return;busy=true;const current=epoch;
    try{
      const data=await api('/calls');if(current!==epoch)return;logged=true;$('login').hidden=true;$('dashboard').hidden=false;
      $('connection').textContent='● Na żywo';$('metrics').textContent=`Buddy: ${data.mode} · Director: ${data.director_mode} · World AI: ${data.world_mode} · ${data.calls.length}/200 wywołań`;
      $('world-location').textContent='Świat na żywo / '+(data.world_state?.location_id??'brak sesji');
      $('world-state').textContent=JSON.stringify(data.world_state??{},null,2);
      renderNpcs(data.world_state,data.world_text_languages);
      $('empty').hidden=data.calls.length>0;
      if($('follow').checked||!data.calls.some(row=>row.id===selected))selected=data.calls[0]?.id||null;
      $('call-list').replaceChildren();
      for(const row of data.calls){
        const button=document.createElement('button');button.className='call'+(row.id===selected?' active':'');
        const title=document.createElement('strong');title.dataset.preserveOriginal='';title.textContent=(row.kind==='asset'?'[Asset '+(row.asset?.source??row.provider)+'] ':row.kind==='world'?'[World AI '+(row.plan_source??row.provider)+'] ':row.kind==='director'?'[Director '+(row.quest_type??'?')+'] ':'['+(row.npc_id??'NPC')+' '+(row.guard_status??'?')+'] ')+(row.kind==='buddy'?window.chessCorpOriginal(row.message,row.language):window.chessCorpT(row.message)).slice(0,90)||window.chessCorpT('Wywołanie Buddy');
        const meta=document.createElement('span');meta.textContent=`${new Date(row.started_at).toLocaleTimeString(window.chessCorpGetLanguage()==='en'?'en-GB':'pl-PL')} · ${row.model}`;
        const status=document.createElement('span');status.className=row.state;status.textContent=`${row.state} · ${row.elapsed_ms===null?'w toku':row.elapsed_ms+' ms'} · tokeny: ${row.usage?.total_tokens??'—'}`;
        button.append(title,meta,status);button.addEventListener('click',()=>{$('follow').checked=false;selected=row.id;refresh();});$('call-list').append(button);
      }
      if(selected){const detail=jury?data.calls.find(row=>row.id===selected):await api('/calls/'+selected);if(current!==epoch)return;show(detail);}
      else{$('detail').hidden=true;$('selection-help').hidden=false;}
    }catch(error){if(error.status===401||error.status===403)lock(logged?error.message:'');else $('connection').textContent='Brak połączenia — ponawiam odczyt…';}
    finally{busy=false;}
  }
  window.addEventListener('chess-language-change',()=>{if(logged)refresh();});
  $('login-form').addEventListener('submit',async event=>{
    event.preventDefault();$('login-error').textContent='';
    try{await api('/login',{method:'POST',body:JSON.stringify({token:$('token').value})});$('token').value='';logged=true;await refresh();}
    catch(error){$('token').value='';$('login-error').textContent=error.message;}
  });
  $('logout').addEventListener('click',async()=>{try{await api('/logout',{method:'POST'});}finally{lock();}});
  $('new-demo').addEventListener('click',async()=>{
    try{const data=await api('/demo',{method:'POST'});$('jury-token').value=data.jury_token;$('demo-game').href=data.game_url;$('demo-access').hidden=false;$('demo-status').textContent='Sesja gotowa. Użyj linku gry demonstracyjnej powyżej.';}
    catch(error){$('demo-status').textContent=error.message;}
  });
  $('revoke').addEventListener('click',async()=>{
    try{await api('/demo/revoke',{method:'POST'});$('jury-token').value='';$('demo-access').hidden=true;$('demo-status').textContent='Dostęp jury cofnięty.';}
    catch(error){$('demo-status').textContent=error.message;}
  });
  $('asset-regenerate').addEventListener('click',async()=>{
    const button=$('asset-regenerate');button.disabled=true;$('asset-clear').disabled=true;
    $('asset-action-status').textContent='Generowanie Meta… Zachowuję poprzedni asset do czasu poprawnego wyniku.';
    try{const data=await api('/asset/generate',{method:'POST',body:JSON.stringify({asset_id:$('asset-choice').value,refresh:true,request_id:crypto.randomUUID().replaceAll('-','')})});
      $('asset-action-status').textContent='Nowy asset gotowy. Gra odświeży go automatycznie. '+data.asset.id;await refresh();
    }catch(error){$('asset-action-status').textContent=error.message;}
    finally{button.disabled=false;$('asset-clear').disabled=false;}
  });
  $('asset-clear').addEventListener('click',async()=>{
    if(!confirm(window.chessCorpT('Usunąć tylko wygenerowane pliki tego assetu? Oryginały i liczniki kosztów pozostaną.')))return;
    try{await api('/asset/clear',{method:'POST',body:JSON.stringify({asset_id:$('asset-choice').value})});$('asset-action-status').textContent='Pliki usunięte. Gra użyje grafiki zastępczej do następnej regeneracji.';await refresh();}
    catch(error){$('asset-action-status').textContent=error.message;}
  });
  refresh();setInterval(()=>{if(logged)refresh();},1000);
})();
