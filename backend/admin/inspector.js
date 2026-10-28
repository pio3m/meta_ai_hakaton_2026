(() => {
  const jury=location.pathname.replace(/\/$/,'')==='/admin/jury';
  const base=jury?'/admin/jury/api':'/admin/api';
  const $=id=>document.getElementById(id);
  let logged=false, selected=null, busy=false, epoch=0;
  $('scope').textContent=jury?'Jury / tylko sesja demo':'Właściciel';
  $('owner-controls').hidden=jury;
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
    for(const id of ['prompt','reply','message','context','error','facts'])$(id).replaceChildren();
    $('jury-token').value='';$('demo-access').hidden=true;$('login-error').textContent=message;
  }
  function tokenText(usage){return usage?`${usage.prompt_tokens??'?'} wej. / ${usage.completion_tokens??'?'} wyj. / ${usage.total_tokens??'?'} razem`:'brak danych';}
  function show(row){
    $('detail').hidden=false;$('selection-help').hidden=true;
    const fields={Czas:new Date(row.started_at).toLocaleString('pl-PL'),Stan:row.state,Dostawca:row.provider,Model:row.model,'Czas wykonania':row.elapsed_ms===null?'w toku':`${row.elapsed_ms} ms`,Tokeny:tokenText(row.usage),'Status HTTP Meta':row.upstream_status??'—'};
    if(!jury)fields.Sesja=row.session_id;
    $('facts').replaceChildren();
    for(const [key,value] of Object.entries(fields)){
      const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=key;dd.textContent=value;$('facts').append(dt,dd);
    }
    $('context').textContent=JSON.stringify(row.context,null,2);
    $('message').textContent=row.message;
    $('reply').textContent=row.reply??(row.state==='pending'?'Buddy pisze…':'Brak odpowiedzi');
    if(row.reply_truncated)$('reply').textContent+='\n[Podgląd ucięty do 16000 znaków]';
    $('error').textContent=row.error||'Brak';
    if(!jury){
      $('sent-note').textContent=row.sent_to_model?'Payload z miejsca wykonania HTTP; sekrety są maskowane.':row.provider==='mock'?'Symulacja mock. Ten prompt NIE został wysłany do modelu.':'Żądanie nie zostało wysłane do modelu.';
      $('prompt').textContent=row.request_payload?JSON.stringify(row.request_payload,null,2):'Brak wysłanego payloadu.';
    }
  }
  async function refresh(){
    if(busy)return;busy=true;const current=epoch;
    try{
      const data=await api('/calls');if(current!==epoch)return;logged=true;$('login').hidden=true;$('dashboard').hidden=false;
      $('connection').textContent='● Na żywo';$('metrics').textContent=`Tryb: ${data.mode} · ${data.calls.length}/200 wywołań`;
      $('empty').hidden=data.calls.length>0;
      if($('follow').checked||!data.calls.some(row=>row.id===selected))selected=data.calls[0]?.id||null;
      $('call-list').replaceChildren();
      for(const row of data.calls){
        const button=document.createElement('button');button.className='call'+(row.id===selected?' active':'');
        const title=document.createElement('strong');title.textContent=row.message.slice(0,70)||'Wywołanie Buddy';
        const meta=document.createElement('span');meta.textContent=`${new Date(row.started_at).toLocaleTimeString('pl-PL')} · ${row.model}`;
        const status=document.createElement('span');status.className=row.state;status.textContent=`${row.state} · ${row.elapsed_ms===null?'w toku':row.elapsed_ms+' ms'} · tokeny: ${row.usage?.total_tokens??'—'}`;
        button.append(title,meta,status);button.addEventListener('click',()=>{$('follow').checked=false;selected=row.id;refresh();});$('call-list').append(button);
      }
      if(selected){const detail=jury?data.calls.find(row=>row.id===selected):await api('/calls/'+selected);if(current!==epoch)return;show(detail);}
      else{$('detail').hidden=true;$('selection-help').hidden=false;}
    }catch(error){if(error.status===401||error.status===403)lock(logged?error.message:'');else $('connection').textContent='Brak połączenia — ponawiam odczyt…';}
    finally{busy=false;}
  }
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
  refresh();setInterval(()=>{if(logged)refresh();},1000);
})();
