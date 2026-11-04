(() => {
 const admin=location.pathname.startsWith('/admin'),jury=location.pathname.includes('/jury');
 const key=admin?(jury?'chess-corp-jury-language':'chess-corp-admin-language'):'chess-corp-language';
 let lang=admin&&!jury?'pl':'en',pairs={},patterns=[],reverse={};
 try{lang=localStorage.getItem(key)||lang;}catch{}
 if(!['en','pl'].includes(lang))lang='en';
 window.chessCorpGetLanguage=()=>lang;
 const translate=(value,depth=0)=>{
  const text=String(value),trim=text.trim();
  if(trim.startsWith('[PL original]')||trim.startsWith('[EN oryginał]')||trim.startsWith('[Original /'))return text;
  let result=lang==='pl'?(reverse[trim]??trim):(pairs[trim]??null);
  if(result===null&&depth<5){for(const [regex,replacement] of patterns){const m=trim.match(regex);if(m){result=replacement.replace(/\$(\d+)/g,(_,n)=>translate(m[Number(n)],depth+1));break;}}}
  return result===null?text:text.replace(trim,result);
 };
 window.chessCorpT=translate;
 window.chessCorpIsAuthored=value=>Object.hasOwn(pairs,String(value).trim())||Object.hasOwn(reverse,String(value).trim());
 window.chessCorpOriginal=(text,source)=>source===lang?text:`[${source==='pl'?'PL original':source==='en'?'EN original':'Original / language unknown'}] ${text}`;
 const saved=new WeakMap();let refreshing=false;
 function refresh(){
  if(refreshing||!document.body)return;refreshing=true;
  document.documentElement.lang=lang;
  const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
  while(walker.nextNode()){
   const node=walker.currentNode;if(node.parentElement.closest('script,style,pre,code,textarea,[data-preserve-original]'))continue;
   let state=saved.get(node);if(!state||node.textContent!==state.last)state={source:node.textContent};
   const next=translate(state.source);state.last=next;saved.set(node,state);if(node.textContent!==next)node.textContent=next;
  }
  const select=document.getElementById('admin-language');if(select)select.value=lang;
  refreshing=false;
 }
 window.chessCorpSetLanguage=value=>{if(!['en','pl'].includes(value))return;lang=value;try{localStorage.setItem(key,value);}catch{}refresh();window.dispatchEvent(new CustomEvent('chess-language-change',{detail:value}));};
 // SDL pointer coordinates include CSS letterboxing; hit-test the visible canvas content.
 if(!admin)document.addEventListener('pointerdown',event=>{
  if(event.button!==0||!document.getElementById('chess-start')?.hidden)return;
  const canvas=document.getElementById('canvas');if(!canvas)return;
  const rect=canvas.getBoundingClientRect(),scale=Math.min(rect.width/canvas.width,rect.height/canvas.height);
  const x=(event.clientX-rect.left-(rect.width-canvas.width*scale)/2)/scale;
  const y=(event.clientY-rect.top-(rect.height-canvas.height*scale)/2)/scale;
  if(x>=30&&x<=100&&y>=80&&y<=103)window.chessCorpSetLanguage(x<64?'en':'pl');
 },true);
 function ready(){
  const select=document.getElementById('admin-language');if(select){select.value=lang;select.addEventListener('change',()=>window.chessCorpSetLanguage(select.value));}
  new MutationObserver(refresh).observe(document.body,{subtree:true,childList:true,characterData:true});refresh();
 }
 fetch(admin?'/admin/assets/i18n.json':'/i18n.json').then(r=>r.json()).then(c=>{pairs=c.pairs;reverse=Object.fromEntries(Object.entries(pairs).map(([k,v])=>[v,k]));patterns=c.patterns.map(([p,r])=>[new RegExp('^(?:'+p+')$'),r]);refresh();});
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',ready);else ready();
})();
