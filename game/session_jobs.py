"""Fresh session errands; deterministic collection and one-time wallet rewards."""
import asyncio,math,os
from game.chat import send_request
from game.job_contract import validate_jobs,objects_for_jobs,replay_jobs
from game.ui import CYAN,GOLD,WHITE
from game.i18n import language
NAMES={'corporate_street':'ULICA','bar':'BAR','hacker_hideout':'KRYJÓWKA','corporate_lobby':'LOBBY'}
class SessionJobs:
 def __init__(self,session_id):
  self.session_id=session_id;self.state='idle';self.task=None;self.report_task=None;self.plan=None;self.objects=[];self.events=[];self.collected=set();self.paid=set();self.open=False;self.error='';self.call_id=None;self.plan_language='und';self.request_language='en'
 def update(self,game):
  if os.getenv('CHESS_CORP_WORLD_NETWORK','true').lower()=='false':return
  if self.state=='idle':
   try:self.request_language=language();self.task=asyncio.get_running_loop().create_task(send_request({'session_id':self.session_id,'language':self.request_language},'/api/director/jobs'));self.state='pending'
   except RuntimeError:return
  if self.task and self.task.done():
   try:
    data=self.task.result()
    if data.get('error') or data.get('validation',{}).get('valid') is not True:raise ValueError(data.get('error','Plan niezatwierdzony'))
    validate_jobs(data['plan']);self.plan_language=data.get('language','und');self.plan=data['plan'];self.objects=objects_for_jobs(self.plan);self.call_id=data['call_id'];self.state='active'
   except Exception as e:self.error=str(e)[:140];self.state='error'
   self.task=None
  if self.report_task and self.report_task.done():
   try:self.report_task.result()
   except Exception:pass
   self.report_task=None
 def interact(self,game):
  if self.state!='active':return False
  obj=next((o for o in self.objects if o['id'] not in self.collected and o['location_id']==game.locations.id and math.dist(o['position'],game.player.position)<=38),None)
  if not obj:return False
  self.events.append({'object_id':obj['id'],'location_id':game.locations.id,'position':list(game.player.position)})
  state=replay_jobs(self.plan,self.events);self.collected=set(state['collected'])
  for job in self.plan['jobs']:
   if job['id'] in state['completed'] and job['id'] not in self.paid:
    self.paid.add(job['id']);game.adventure.credits+=job['reward'];game.audio.play('credits');game.adventure.event(job['title']+': +'+str(job['reward'])+' KR',game.living)
  game.audio.play('purchase')
  try:self.report_task=asyncio.get_running_loop().create_task(send_request({'session_id':self.session_id,'call_id':self.call_id,'events':list(self.events)},'/api/director/jobs/execution'))
  except RuntimeError:pass
  return True
 def draw(self,screen,ui,game):
  import pygame
  modal=game.adventure.shop_open or game.locations.map_open or game.director.answer_open or self.open
  for obj in self.objects if not modal else []:
   if obj['id'] in self.collected or obj['location_id']!=game.locations.id:continue
   x,y=obj['position'];pygame.draw.rect(screen,(20,38,49),(int(x-11),int(y-22),22,22));pygame.draw.rect(screen,GOLD,(int(x-11),int(y-22),22,22),2)
   ui.text(screen,'+', (x-4,y-19),CYAN)
   if math.dist(obj['position'],game.player.position)<=42:ui.text(screen,'[E] '+ui.ai_text(obj['label'],self.plan_language),(max(20,min(730,x-50)),y-47),GOLD,True)
  ui.text(screen,'J: zlecenia '+str(len(self.paid))+'/2',(30,484),GOLD,True)
  if not self.open:return
  ui.panel(screen,(100,130,760,350));ui.text(screen,'NOWE ZLECENIA / TA SESJA',(124,150),CYAN)
  if not self.plan:
   ui.text(screen,'Director wymyśla nowe zlecenia…' if self.state=='pending' else 'Nowe zlecenia niedostępne. R: nowa sesja.',(124,195),GOLD)
  else:
   for i,job in enumerate(self.plan['jobs']):
    y=190+i*125;count=sum(o['id'] in self.collected for o in self.objects if o['job_id']==job['id'])
    ui.text(screen,('GOTOWE / ' if job['id'] in self.paid else '')+ui.ai_text(job['title'],self.plan_language),(124,y),GOLD)
    for n,line in enumerate(ui.wrap(ui.ai_text(job['description'],self.plan_language),680)[:2]):ui.text(screen,line,(124,y+24+n*20),WHITE)
    places=', '.join(NAMES[p['location_id']] for p in job['placements']);ui.text(screen,f"{places} | {count}/{len(job['placements'])} | {job['reward']} KR",(124,y+73),CYAN,True)
  ui.text(screen,'E przy przedmiocie: odbierz. Wypłata automatyczna. J / Esc: zamknij.',(124,450),WHITE,True)
 def cancel(self):
  for t in (self.task,self.report_task):
   if t:t.cancel()
