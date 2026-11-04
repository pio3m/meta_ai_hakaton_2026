// Browser QA instrumentation only: observes real Web Audio output; does not synthesize sound.
(() => {
 const qa=window.__audioQA={contexts:[],nodes:[],samples:[],chunks:[]};
 const Native=window.AudioContext;
 if(Native)window.AudioContext=new Proxy(Native,{construct(target,args,newTarget){const c=Reflect.construct(target,args,newTarget);qa.contexts.push(c);return c;}});
 const connect=AudioNode.prototype.connect;
 AudioNode.prototype.connect=function(destination,...rest){
  const result=connect.call(this,destination,...rest);
  if(destination instanceof AudioDestinationNode&&!qa.nodes.some(n=>n.source===this)){
   const analyser=this.context.createAnalyser();analyser.fftSize=2048;
   connect.call(this,analyser);
   const sink=this.context.createMediaStreamDestination();connect.call(this,sink);
   qa.nodes.push({source:this,analyser,sink});
  }
  return result;
 };
 qa.measure=()=>{
  let rms=0,peak=0;
  for(const node of qa.nodes){const values=new Float32Array(node.analyser.fftSize);node.analyser.getFloatTimeDomainData(values);let sum=0;for(const v of values){sum+=v*v;peak=Math.max(peak,Math.abs(v));}rms=Math.max(rms,Math.sqrt(sum/values.length));}
  return {rms,peak,contexts:qa.contexts.map(c=>c.state),outputNodes:qa.nodes.length};
 };
 setInterval(()=>{qa.samples.push({time:performance.now(),...qa.measure()});if(qa.samples.length>6000)qa.samples.shift();},100);
 qa.startRecording=()=>{if(!qa.nodes.length)return false;qa.recorder=new MediaRecorder(qa.nodes[0].sink.stream,{mimeType:'audio/webm;codecs=opus',audioBitsPerSecond:64000});qa.recorder.ondataavailable=e=>{if(e.data.size)qa.chunks.push(e.data);};qa.recorder.start(1000);return true;};
 qa.finishRecording=()=>new Promise(resolve=>{if(!qa.recorder){resolve('');return;}qa.recorder.onstop=async()=>{const blob=new Blob(qa.chunks,{type:'audio/webm'});const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.readAsDataURL(blob);};qa.recorder.stop();});
 qa.frames=[];let previous=0;function frame(now){if(previous)qa.frames.push(now-previous);previous=now;if(qa.frames.length>1200)qa.frames.shift();requestAnimationFrame(frame);}requestAnimationFrame(frame);
})();
