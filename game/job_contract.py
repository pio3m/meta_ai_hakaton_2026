"""Closed, shared session-job contract. All coordinates and rewards are engine-owned data."""
from math import dist,isfinite
POINTS={
 'corporate_street':{'A':[310,478],'B':[620,478]},
 'bar':{'A':[830,430],'B':[660,480]},
 'hacker_hideout':{'A':[730,475],'B':[470,430]},
 'corporate_lobby':{'A':[325,475],'B':[610,480]},
}
def exact(value,keys):
 if not isinstance(value,dict) or set(value)!=set(keys):raise ValueError('Unexpected job fields')
def validate_jobs(plan):
 exact(plan,('schema_version','jobs'))
 if type(plan['schema_version']) is not int or plan['schema_version']!=1:raise ValueError('Unknown session job version')
 if not isinstance(plan['jobs'],list) or len(plan['jobs'])!=2:raise ValueError('Two session jobs required')
 seen=set();ids=set()
 for job in plan['jobs']:
  exact(job,('id','title','description','item_label','reward','placements'))
  if job['id'] not in ('job_a','job_b') or job['id'] in ids:raise ValueError('Invalid job ID')
  ids.add(job['id'])
  for field,limit in [('title',60),('description',180),('item_label',28)]:
   if not isinstance(job[field],str) or not 3<=len(job[field])<=limit or not job[field].isprintable():raise ValueError('Invalid job text')
  if type(job['reward']) is not int or not 15<=job['reward']<=45:raise ValueError('Invalid reward')
  if not isinstance(job['placements'],list) or not 1<=len(job['placements'])<=2:raise ValueError('Invalid item count')
  for placement in job['placements']:
   exact(placement,('location_id','slot'));location=placement['location_id'];slot=placement['slot']
   if location not in POINTS or slot not in POINTS[location] or (location,slot) in seen:raise ValueError('Invalid or duplicate approved placement')
   seen.add((location,slot))
 return plan

def objects_for_jobs(plan):
 validate_jobs(plan)
 return [{**p,'position':list(POINTS[p['location_id']][p['slot']]),'id':j['id']+'_'+str(i),'job_id':j['id'],'label':j['item_label']} for j in plan['jobs'] for i,p in enumerate(j['placements'])]

def replay_jobs(plan,events):
 objects={o['id']:o for o in objects_for_jobs(plan)};collected=set();completed=[];reward=0
 for event in events:
  exact(event,('object_id','location_id','position'))
  obj=objects.get(event['object_id']);pos=event['position']
  if not obj or obj['id'] in collected or event['location_id']!=obj['location_id']:raise ValueError('Invalid collection')
  if not isinstance(pos,(tuple,list)) or len(pos)!=2 or any(type(v) not in (int,float) or not isfinite(v) for v in pos) or dist(pos,obj['position'])>38:raise ValueError('Object out of reach')
  collected.add(obj['id'])
 for job in plan['jobs']:
  if all(o['id'] in collected for o in objects.values() if o['job_id']==job['id']):completed.append(job['id']);reward+=job['reward']
 return {'collected':sorted(collected),'completed':completed,'credits_awarded':reward}
