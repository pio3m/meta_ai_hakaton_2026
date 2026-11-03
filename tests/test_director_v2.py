import asyncio
import copy
import json
import itertools
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.settings import Settings
from backend.director import mock_plan,mock_plan_v2,director_payload
from backend.director_models import parse_plan,load_rules,validate_scene,DirectorPlanV2,DirectorRequest
from game.director import Director,validate_plan
from game.director_contract import objects_for_plan,initial_execution,execute_event,puzzle_answer,puzzle_question
from game.data import load_content
from game.quests import Quest

KINDS=('COLLECT','SEQUENCE','LOGIC_PUZZLE')
BODY={'session_id':'poc035-integration-session','context':{'quest_status':'completed','has_badge':True}}
OWNER='poc035-test-owner-0123456789abcdef'


def event(obj,answer='',action='interact'):
    return {'action':action,'object_id':obj['id'],'position':obj['position'],'answer':answer}


@pytest.mark.parametrize('kind',KINDS)
def test_v2_contract_both_sides(kind):
    plan=mock_plan_v2('test',kind);model=parse_plan(json.dumps(plan));rules,scene=load_rules()
    objects=validate_scene(model,rules,scene)
    assert objects==validate_plan(plan,scene,rules) and len(objects)==(3 if kind=='SEQUENCE' else 1)
    assert model.model_dump()==plan


@pytest.mark.parametrize('mutation',[
    lambda p:p.update(schema_version=True),lambda p:p.update(schema_version=3),
    lambda p:p.update(quest_type='RUN_CODE'),lambda p:p.update(sequence=['terminal_a']*3),
    lambda p:p.update(sequence=['terminal_a','terminal_b']),
    lambda p:p['place_objects'][0].update(id='buddy'),
    lambda p:p['place_objects'][0].update(spawn_point='rooftop'),
    lambda p:p['place_objects'][0].update(position=[1,2]),
    lambda p:p['place_objects'][0].update(action='spawn_npc'),
    lambda p:p['place_objects'][0].update(appearance='data_chip'),
    lambda p:p['place_objects'][1].update(spawn_point=p['place_objects'][0]['spawn_point']),
    lambda p:p['place_objects'][1].update(id=p['place_objects'][0]['id']),
    lambda p:p.update(puzzle={'template':'SUM','a':2,'b':3,'flavor':'Test'}),
    lambda p:p['create_quest']['quest']['completion'].update(type='collect_object'),
    lambda p:p['create_quest']['quest'].update(objective='x'*101),
])
def test_reject_unsafe_v2(mutation):
    plan=mock_plan_v2('test','SEQUENCE');mutation(plan);rules,scene=load_rules()
    with pytest.raises(ValueError):parse_plan(json.dumps(plan))
    with pytest.raises(ValueError):validate_plan(plan,scene,rules)


@pytest.mark.parametrize('mutation',[
    lambda p:p.update(template='PYTHON'),lambda p:p.update(a=True),lambda p:p.update(b=0),
    lambda p:p.update(a=21),lambda p:p.update(template='DIFFERENCE',a=1,b=9),
    lambda p:p.update(answer='15'),lambda p:p.update(flavor='bad\ntext'),
])
def test_reject_unverifiable_puzzle(mutation):
    plan=mock_plan_v2('test','LOGIC_PUZZLE');mutation(plan['puzzle']);rules,scene=load_rules()
    with pytest.raises(ValueError):parse_plan(json.dumps(plan))
    with pytest.raises(ValueError):validate_plan(plan,scene,rules)


@pytest.mark.parametrize('template',['SUM','DIFFERENCE','NEXT_NUMBER'])
def test_all_puzzle_parameters_have_one_deterministic_answer(template):
    for a in range(1,21):
        for b in range(1,10):
            if template=='DIFFERENCE' and a<b:continue
            plan=mock_plan_v2('test','LOGIC_PUZZLE');plan['puzzle'].update(template=template,a=a,b=b)
            parse_plan(json.dumps(plan))
            rules,scene=load_rules();objects=objects_for_plan(plan,scene,rules)
            state=initial_execution()
            wrong=execute_event(state,plan,objects,event(objects[0],'999','answer'),scene)
            assert wrong['status']=='active' and wrong['mistakes']==1
            answer=puzzle_answer(plan['puzzle'])
            done=execute_event(wrong,plan,objects,event(objects[0],' 00'+str(answer)+' ','answer'),scene)
            assert done['status']=='completed' and done['attempts']==2
            assert puzzle_question(plan['puzzle'])


@pytest.mark.parametrize('order',list(itertools.permutations(['terminal_a','terminal_b','terminal_c'])))
def test_every_sequence_order_reset_and_completion(order):
    plan=mock_plan_v2('test','SEQUENCE');plan['sequence']=list(order)
    rules,scene=load_rules();objects=objects_for_plan(plan,scene,rules);by_id={o['id']:o for o in objects}
    state=execute_event(initial_execution(),plan,objects,event(by_id[order[0]]),scene)
    state=execute_event(state,plan,objects,event(by_id[order[0]]),scene)
    assert state['progress']==0 and state['mistakes']==1
    for ident in order:state=execute_event(state,plan,objects,event(by_id[ident]),scene)
    assert state['status']=='completed' and state['progress']==3
    assert execute_event(state,plan,objects,event(by_id[order[0]]),scene)==state


@pytest.mark.parametrize('kind',KINDS)
def test_api_game_inspector_complete_flow(kind):
    scene,data,_=load_content();quest=Quest(data)
    app=create_app(Settings(inspector_token=OWNER))
    with TestClient(app) as client:
        async def transport(payload,path):
            r=await asyncio.to_thread(lambda:client.post(path,json=payload))
            return r.json() if r.status_code==200 else {'error':r.json()['detail']}
        async def flush(d):
            for _ in range(3):
                d._poll_execution()
                if d.execution_task:await d.execution_task
            d._poll_execution()
        async def run():
            d=Director(scene,transport);d.mock_type=kind
            assert not d.start(quest,BODY['session_id'])
            for target in ['buddy','corporate_entrance','buddy']:quest.interact(target)
            assert d.start(quest,BODY['session_id'])
            await d.task;d.poll(quest)
            assert d.state=='active' and d.quest_type==kind and not d.interact((900,480),quest)
            if kind=='COLLECT':
                assert d.collect(d.object['position'],quest)
            elif kind=='SEQUENCE':
                by_id={o['id']:o for o in d.objects}
                wrong=next(o for o in d.objects if o['id']!=d.plan['sequence'][0])
                d.interact(wrong['position'],quest)
                assert d.execution['mistakes']==1 and d.execution['progress']==0
                for ident in d.plan['sequence']:d.interact(by_id[ident]['position'],quest)
            else:
                pos=d.objects[0]['position'];d.interact(pos,quest)
                assert d.answer_open
                d.insert_answer('0');d.submit_answer(pos,quest)
                assert d.answer_open and d.execution['mistakes']==1
                d.insert_answer(str(puzzle_answer(d.plan['puzzle'])));d.submit_answer(pos,quest)
                assert not d.answer_open
            await flush(d)
            assert not d.execution_error and d.state=='completed'
            assert not d.interact(d.objects[0]['position'],quest)
            assert quest.reward_count==1 and quest.inventory=={'employee_badge'}
            client.post('/admin/api/login',json={'token':OWNER})
            row=client.get('/admin/api/calls/'+d.call_id).json()
            assert row['execution']['status']=='completed' and row['quest_type']==kind and row['validation']['valid']
            assert 'answer' not in row['execution'] and row['sent_to_model'] is False
            # Cannot substitute another session, change the old prefix or claim a remote interaction.
            payload={'session_id':BODY['session_id'],'call_id':d.call_id,'events':d.trace}
            assert client.post('/api/director/execution',json={**payload,'session_id':'another-session'}).status_code==404
            changed=copy.deepcopy(d.trace);changed[0]['position']=[36,422]
            assert client.post('/api/director/execution',json={**payload,'events':changed}).status_code==409
            assert client.post('/api/director/execution',json=payload).status_code==200
            jury=app.state.inspector.list(BODY['session_id'],jury=True)[0]
            assert jury['execution']['status']=='completed' and 'request_payload' not in jury
            assert 'director_execution_events' not in jury
            d.cancel()
        asyncio.run(run())


def test_legacy_v1_still_executes_and_reports():
    class Legacy:
        async def generate(self,*args):return json.dumps(mock_plan('legacy'))
    app=create_app(Settings(),director_provider=Legacy())
    with TestClient(app) as client:
        result=client.post('/api/director',json=BODY).json()
        assert result['plan']['schema_version']==1
        rules,scene=load_rules();objects=objects_for_plan(result['plan'],scene,rules)
        response=client.post('/api/director/execution',json={'session_id':BODY['session_id'],'call_id':result['call_id'],'events':[event(objects[0])]})
        assert response.json()['execution']['status']=='completed'


def test_bad_execution_is_rejected_without_mutation():
    app=create_app(Settings())
    with TestClient(app) as client:
        result=client.post('/api/director',json={**BODY,'mock_type':'LOGIC_PUZZLE'}).json()
        payload={'session_id':BODY['session_id'],'call_id':result['call_id'],'events':[{'action':'answer','object_id':'puzzle_terminal','position':[36,422],'answer':'15'}]}
        assert client.post('/api/director/execution',json=payload).status_code==422
        payload['events'][0]['position']=[780,452];payload['events'][0]['code']='bad'
        assert client.post('/api/director/execution',json=payload).status_code==422
        assert app.state.inspector.get(result['call_id'])['execution']['events']==0


def test_scene_v2_collision_and_boundaries():
    plan=mock_plan_v2('test','SEQUENCE');rules,scene=load_rules()
    for position in ([540,440],[0,0],[110,452]):
        bad=copy.deepcopy(rules);bad['spawn_points']['center_side']=position
        with pytest.raises(ValueError):objects_for_plan(plan,scene,bad)
        with pytest.raises(ValueError):validate_scene(parse_plan(json.dumps(plan)),bad,scene)


def test_v2_schema_closed_and_meta_guard_still_off():
    schema=DirectorPlanV2.model_json_schema()
    def check(node):
        if isinstance(node,dict):
            assert 'oneOf' not in node and 'allOf' not in node
            if node.get('type')=='object':
                assert node['additionalProperties'] is False
                assert set(node['required'])==set(node['properties'])
            for value in node.values():check(value)
        elif isinstance(node,list):
            for value in node:check(value)
    check(schema)
    payload=director_payload(DirectorRequest(**BODY),Settings(),load_rules()[0])
    assert payload['response_format']['json_schema']['schema']==schema
    assert Settings().director_allow_paid_requests is False


def test_game_answer_input_escape_and_reset():
    import os
    os.environ['SDL_VIDEODRIVER']='dummy';os.environ['SDL_AUDIODRIVER']='dummy'
    import pygame
    from main import Game
    pygame.init();screen=pygame.display.set_mode((960,540))
    try:
        game=Game();game.key(pygame.K_F4);assert game.director.mock_type=='SEQUENCE'
        game.key(pygame.K_F4);assert game.director.mock_type=='LOGIC_PUZZLE'
        for target in ['buddy','corporate_entrance','buddy']:game.quest.interact(target)
        d=game.director;d.plan=mock_plan_v2('test','LOGIC_PUZZLE');d.objects=objects_for_plan(d.plan,game.scene,d.rules);d.state='active'
        game.player.x,game.player.y=d.objects[0]['position']
        game.key(pygame.K_e);assert d.answer_open
        game.text_input('0');game.key(pygame.K_RETURN);assert d.answer_open and d.execution['mistakes']==1
        game.key(pygame.K_ESCAPE);assert not d.answer_open and d.state=='active'
        game.key(pygame.K_e);game.text_input('e15x');assert d.answer=='15';game.key(pygame.K_BACKSPACE);game.text_input('5');game.key(pygame.K_RETURN)
        assert d.state=='completed' and not d.answer_open
        game.draw(screen)
        game.key(pygame.K_r);assert game.director.state=='idle' and not game.quest.complete
    finally:pygame.quit()


def test_jury_execution_is_scoped_and_does_not_expose_answers():
    app=create_app(Settings(inspector_token=OWNER))
    with TestClient(app) as owner, TestClient(app) as jury:
        owner.post('/admin/api/login',json={'token':OWNER})
        grant=owner.post('/admin/api/demo').json();session=grant['game_url'].split('=',1)[1]
        other=owner.post('/api/director',json={**BODY,'session_id':'private-other-session'}).json()
        demo=owner.post('/api/director',json={**BODY,'session_id':session,'mock_type':'LOGIC_PUZZLE'}).json()
        rules,scene=load_rules();obj=objects_for_plan(demo['plan'],scene,rules)[0]
        trace=[event(obj,'PRIVATE_ANSWER','answer')]
        payload={'session_id':session,'call_id':demo['call_id'],'events':trace}
        assert owner.post('/api/director/execution',json=payload).status_code==200
        assert jury.get('/admin/jury/api/calls').status_code==401
        jury.post('/admin/jury/api/login',json={'token':grant['jury_token']})
        rows=jury.get('/admin/jury/api/calls').json()['calls']
        assert len(rows)==1 and rows[0]['execution']['mistakes']==1
        encoded=json.dumps(rows)
        assert 'PRIVATE_ANSWER' not in encoded and other['call_id'] not in encoded
        assert 'request_payload' not in encoded and 'session_id' not in encoded
        assert jury.get('/admin/api/calls/'+demo['call_id']).status_code==401
        assert owner.post('/admin/api/demo/revoke').status_code==200
        assert jury.get('/admin/jury/api/calls').status_code==401
