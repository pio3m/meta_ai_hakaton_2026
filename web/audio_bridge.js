/* The first real user gesture unlocks only AudioContexts already used by SDL.
   No separate music engine, extra context, network request or visible UI. */
(() => {
  let gestureSeen=false;
  const contexts=new Set();
  const resume=context=>{if(context.state==='suspended'){try{context.resume().catch(()=>{});}catch{}}};
  for(const key of ['AudioContext','webkitAudioContext']){
    const Native=window[key];if(!Native)continue;
    window[key]=new Proxy(Native,{construct(target,args,newTarget){
      const context=Reflect.construct(target,args,newTarget);contexts.add(context);
      context.addEventListener('statechange',()=>{if(context.state==='closed')contexts.delete(context);});
      if(gestureSeen)resume(context);
      return context;
    }});
  }
  const unlock=event=>{if(!event.isTrusted)return;gestureSeen=true;for(const context of contexts)resume(context);};
  document.addEventListener('pointerdown',unlock,{capture:true,passive:true});
  document.addEventListener('keydown',unlock,{capture:true,passive:true});
  window.chessCorpAudioGestureSeen=()=>gestureSeen;
  window.chessCorpAudioReport=encoded=>{try{window.chessCorpAudioStatus=JSON.parse(encoded);}catch{}};
})();
