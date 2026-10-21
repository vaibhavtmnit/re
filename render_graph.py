"""Render a self-contained offline graph inspector and a compact Mermaid view."""
import json


def render(graph, root):
    embedded = json.dumps(graph, ensure_ascii=True).replace("<", "\\u003c").replace(">", "\\u003e")
    template = r'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SFTR seed knowledge graph</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f4f6fa;color:#18283f;font:15px system-ui,sans-serif}
header{padding:22px 28px;background:#142b46;color:white}h1{font-size:25px;margin:0 0 8px}header p{margin:5px 0;color:#c5d7e9}
nav{display:flex;gap:15px;align-items:center;flex-wrap:wrap;padding:14px 28px;background:white;border-bottom:1px solid #d5deea}
button,select{font:inherit;padding:8px;border:1px solid #b8c8dc;border-radius:5px;background:white;cursor:pointer}
a{color:#235a92}main{display:grid;grid-template-columns:minmax(550px,1fr) 410px;gap:16px;padding:16px}
.canvas,aside{background:white;border:1px solid #dae2ec;border-radius:9px}.canvas{overflow:auto}svg{width:100%;min-width:760px;display:block}
aside{padding:18px;max-height:calc(100vh - 180px);overflow:auto;position:sticky;top:12px}h2{font-size:19px;margin-top:0}
pre{font:12px/1.6 ui-monospace,monospace;white-space:pre-wrap;overflow-wrap:anywhere;background:#f5f7fa;padding:12px;border-radius:5px}
.warn{background:#fff2d9;padding:12px;border-left:3px solid #d49232;font-size:13px}.legend{font-size:12px;color:#52657b;padding:12px 18px}
details{margin-top:12px}summary{cursor:pointer;font-weight:600}.node{cursor:pointer}.node:focus rect{stroke:#102a48;stroke-width:3}
.edge{fill:none;stroke:#b4c1d1;stroke-width:1.2}.edge.source{stroke-dasharray:5 4}
@media(max-width:1050px){main{grid-template-columns:1fr}aside{position:static;max-height:none}}
</style>
<header><h1>SFTR seed knowledge graph</h1><p id="counts"></p><p>Assistant-curated candidates. No approved UK rules or executable release.</p></header>
<nav><label>Focus field <select id="filter"><option value="">All seven fields</option></select></label>
<button id="reset">Reset view</button><a href="graph.json" download>Graph JSON</a><a href="nodes.jsonl" download>Nodes JSONL</a><a href="edges.jsonl" download>Edges JSONL</a><a href="README.md">Readme</a></nav>
<main><section class="canvas"><div class="legend">Blue: fields · Orange: requirement candidates · Green: business context · Purple: sources<br>Solid edges: expression dependencies. Dashed edges: evidence paths collapsed through source spans. Click a node for details.</div><svg id="graph" viewBox="0 0 1120 900" aria-label="Interactive SFTR requirement graph"></svg></section>
<aside id="inspector"><h2>Select a node</h2><p>Inspect exact source passages, conditions, assertions and blockers. The diagram shows a readable projection; the JSON contains the complete provenance graph.</p><div class="warn">All candidates have unresolved scope, qualifications and UK applicability. R08 additionally records an interpretation ambiguity.</div></aside></main>
<script type="application/json" id="data">__GRAPH_DATA__</script>
<script>
'use strict';
const G=JSON.parse(document.getElementById('data').textContent),N=new Map(G.nodes.map(n=>[n.id,n])),E=G.edges;
const byType=t=>G.nodes.filter(n=>n.type===t),out=(id,t)=>E.filter(e=>e.from_id===id&&(!t||e.type===t));
const fields=byType('FieldVersion'),requirements=byType('RequirementVersion'),contexts=byType('ContextDefinition');
const stable=id=>N.get(out(id,'VERSION_OF')[0]?.to_id),label=n=>n.type==='FieldVersion'?stable(n.id).properties.display_name:n.properties.title||n.properties.name||n.id;
const fieldCode=n=>{let f=stable(n.id).properties;return f.table_id+'.'+f.field_number};
const sourceOfSpan=id=>{let a=out(id,'LOCATED_IN')[0]?.to_id,v=out(a,'REPRESENTS')[0]?.to_id;return out(v,'VERSION_OF')[0]?.to_id};
const selector=document.getElementById('filter');fields.forEach(n=>{let o=document.createElement('option');o.value=n.id;o.textContent=fieldCode(n)+' '+label(n);selector.append(o)});
document.getElementById('counts').textContent=`${fields.length} fields · ${requirements.length} candidates · ${G.nodes.length} nodes · ${E.length} edges`;
const svg=document.getElementById('graph'),ns='http://www.w3.org/2000/svg';
function el(tag,attrs,text){let a=document.createElementNS(ns,tag);for(let [k,v] of Object.entries(attrs||{}))a.setAttribute(k,v);if(text!==undefined)a.textContent=text;return a}
function draw(){svg.replaceChildren();const chosen=selector.value;
 const rs=chosen?requirements.filter(r=>out(r.id,'USES_FIELD').some(e=>e.to_id===chosen)):requirements;
 const ids=new Set(rs.flatMap(r=>[...out(r.id,'USES_FIELD'),...out(r.id,'USES_CONTEXT')].map(e=>e.to_id)));
 const ss=new Set(rs.flatMap(r=>out(r.id,'CITES').map(e=>sourceOfSpan(e.to_id))));
 const groups=[fields.filter(f=>!chosen||ids.has(f.id)),rs,contexts.filter(c=>ids.has(c.id)),byType('SourceDocument').filter(s=>ss.has(s.id))];
 const pos=new Map();groups.forEach((group,col)=>group.forEach((n,i)=>pos.set(n.id,{x:15+col*280,y:65+i*82})));
 const links=[];rs.forEach(r=>{for(let e of [...out(r.id,'USES_FIELD'),...out(r.id,'USES_CONTEXT')])links.push({from:r.id,to:e.to_id,type:e.type});
 for(let id of new Set(out(r.id,'CITES').map(e=>sourceOfSpan(e.to_id))))links.push({from:r.id,to:id,type:'source'})});
 links.forEach(e=>{let a=pos.get(e.from),b=pos.get(e.to);if(!a||!b)return;let forward=b.x>a.x,x1=a.x+(forward?245:0),x2=b.x+(forward?0:245);
 let path=el('path',{d:`M${x1},${a.y+27} C${(x1+x2)/2},${a.y+27} ${(x1+x2)/2},${b.y+27} ${x2},${b.y+27}`,class:'edge '+e.type});path.append(el('title',{},e.type));svg.append(path)});
 ['Fields','Requirement candidates','Business context','Evidence sources'].forEach((t,i)=>svg.append(el('text',{x:20+i*280,y:30,fill:'#455e7c','font-size':15,'font-weight':600},t)));
 const colors=['#e5efff','#fff0d5','#e3f4ed','#eee7fa'];groups.forEach((group,col)=>group.forEach(n=>{let p=pos.get(n.id),g=el('g',{class:'node',tabindex:0,role:'button','aria-label':label(n)});
 g.append(el('rect',{x:p.x,y:p.y,width:245,height:56,rx:7,fill:colors[col],stroke:'#b5c3d4'}));
 let title=col===0?fieldCode(n)+' '+label(n):col===1?n.id.split(':')[1]+' '+n.properties.interpretation:label(n);
 let words=title.split(' '),lines=[''];for(let w of words){let j=lines.length-1;if((lines[j]+' '+w).length>32&&lines[j])lines.push(w);else lines[j]+=(lines[j]?' ':'')+w}
 lines.slice(0,3).forEach((line,j)=>g.append(el('text',{x:p.x+10,y:p.y+18+j*15,fill:'#1e3552','font-size':11},line)));
 g.append(el('title',{},title));g.addEventListener('click',()=>inspect(n));g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();inspect(n)}});svg.append(g)}));
 svg.setAttribute('viewBox',`0 0 1120 ${Math.max(440,90+Math.max(...groups.map(g=>g.length))*82)}`);
}
function block(parent,title,value){let d=document.createElement('details');d.open=true;let s=document.createElement('summary');s.textContent=title;d.append(s);let p=document.createElement('pre');p.textContent=typeof value==='string'?value:JSON.stringify(value,null,2);d.append(p);parent.append(d)}
function inspect(n){let panel=document.getElementById('inspector');panel.replaceChildren();let h=document.createElement('h2');h.textContent=n.type==='RequirementVersion'?n.id.split(':')[1]:label(n);panel.append(h);
 if(n.type==='RequirementVersion'){let w=document.createElement('div');w.className='warn';w.textContent='Candidate only: not approved for UK reporting.';panel.append(w);
 block(panel,'Condition',n.properties.when);block(panel,'Assertion',n.properties.assertion);block(panel,'Qualifications',n.properties.unless);
 block(panel,'Open issues',E.filter(e=>e.type==='AFFECTS'&&e.to_id===n.id).map(e=>N.get(e.from_id).properties.description));}
 block(panel,'Node properties',n.properties);
 let citations=n.type==='SourceDocument'?byType('SourceSpan').filter(s=>sourceOfSpan(s.id)===n.id).map(s=>({to_id:s.id,properties:{role:'source span'}})):out(n.id,'CITES');
 for(let e of citations){let span=N.get(e.to_id),doc=N.get(sourceOfSpan(span.id));let a=document.createElement('a');a.href=doc.properties.canonical_uri;a.target='_blank';a.rel='noopener';a.textContent=doc.properties.title;panel.append(a);block(panel,e.properties.role+' · '+span.id,span.properties.content)}
}
selector.addEventListener('change',draw);document.getElementById('reset').addEventListener('click',()=>{selector.value='';draw()});draw();
</script></html>'''
    (root / "graph.html").write_bytes(template.replace("__GRAPH_DATA__", embedded).encode("utf-8"))
    nodes = {n["id"]: n for n in graph["nodes"]}
    lines = ["flowchart LR"]
    names = {}
    for i, n in enumerate(graph["nodes"]):
        if n["type"] not in ["FieldVersion", "RequirementVersion", "ContextDefinition"]:
            continue
        key = f"n{i}"; names[n["id"]] = key
        if n["type"] == "FieldVersion":
            text = n["id"].split(":")[1]
        elif n["type"] == "ContextDefinition":
            text = n["properties"]["name"]
        else:
            text = n["id"].split(":")[1] + " " + n["properties"]["interpretation"]
        lines.append(f'    {key}["{text}"]')
    for e in graph["edges"]:
        if e["type"] in ["USES_FIELD", "USES_CONTEXT"]:
            lines.append(f'    {names[e["from_id"]]} -->|{e["type"]}| {names[e["to_id"]]}')
    (root / "graph.mmd").write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
