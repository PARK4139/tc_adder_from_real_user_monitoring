const search=document.getElementById('search'),cards=[...document.querySelectorAll('.tc')],results=document.getElementById('results');
const nav=document.getElementById('tc-tree'),nodeToggle=document.getElementById('tree-collapse-tcs'),allToggle=document.getElementById('tree-expand-all');
const normalize=text=>text.normalize('NFKC').toLowerCase().replace(/\s+/g,' ').trim();
function parseQuery(value){
 const groups=[[]];
 for(const raw of normalize(value).split(' ').filter(Boolean)){
  if(raw==='|'){if(groups.at(-1).length)groups.push([]);continue;}
  let token=raw,exclude=false;
  if(token.startsWith('!')&&token.length>1){exclude=true;token=token.slice(1);}
  let mode='fuzzy';
  if(token.startsWith("'")){mode='contains';token=token.slice(1);}
  else if(token.startsWith('^')){mode='prefix';token=token.slice(1);}
  if(mode!=='contains'&&token.endsWith('$')){mode=mode==='prefix'?'equal':'suffix';token=token.slice(0,-1);}
  if(!token){token=raw;mode='fuzzy';exclude=false;}
  if(exclude&&mode==='fuzzy')mode='contains';
  groups.at(-1).push({value:token,mode,exclude});
 }
 return groups.filter(group=>group.length);
}
function fuzzyScore(query,text){
 let cursor=0,previous=-2,score=0;
 for(const letter of query){
  const index=text.indexOf(letter,cursor);if(index<0)return null;
  score+=index===previous+1?8:3;
  if(index===0||/[\s_\-/>()]/.test(text[index-1]))score+=4;
  previous=index;cursor=index+letter.length;
 }
 if(text.startsWith(query))score+=20;
 if(text.includes(query))score+=20;
 return score-text.length/20;
}
function termScore(term,fields){
 let best=null;
 for(const field of fields){
  let score=null;
  if(term.mode==='fuzzy')score=fuzzyScore(term.value,field);
  else if(term.mode==='contains'&&field.includes(term.value))score=term.value.length+15;
  else if(term.mode==='prefix'&&field.startsWith(term.value))score=term.value.length+30;
  else if(term.mode==='suffix'&&field.endsWith(term.value))score=term.value.length+25;
  else if(term.mode==='equal'&&field===term.value)score=term.value.length+35;
  if(score!==null&&(best===null||score>best))best=score;
 }
 return best;
}
const allLinks=[...nav.querySelectorAll('a[href^="#"]')],linkById=new Map(allLinks.map(link=>[decodeURIComponent(link.hash.slice(1)),link]));
const cardsData=cards.map((card,index)=>{
 const id=card.id,link=linkById.get(id),title=normalize(card.querySelector('h2').textContent.replace(id,''));
 const fields=[normalize(id),...[...card.querySelectorAll('h2,.tc-meta,li,td,.precondition-details')].map(element=>normalize(element.textContent.replace(id,'')))].filter(Boolean);
 const targets=[],walker=document.createTreeWalker(card,NodeFilter.SHOW_TEXT),texts=[];
 while(walker.nextNode())if(walker.currentNode.textContent.trim())texts.push(walker.currentNode);
 for(const text of texts){const node=document.createElement('span');text.replaceWith(node);node.textContent=text.textContent;targets.push({node,text:text.textContent});}
 return {card,index,id,link,title,fields,targets,navTargets:[],score:0};
});
const recordById=new Map(cardsData.map(record=>[record.id,record]));
const branches=[...nav.querySelectorAll('details')].map(node=>({node,total:node.querySelectorAll('a').length}));
const branchLabels=[];
nav.querySelectorAll('.tree-title,.tree-id,.tree-label').forEach(node=>{
 const text=node.textContent,link=node.closest('a'),record=link?recordById.get(decodeURIComponent(link.hash.slice(1))):null;
 const target={node,text};
 if(record)record.navTargets.push(target);else branchLabels.push(target);
});
const containers=[...nav.querySelectorAll('.tree-children')].map(node=>({node,children:[...node.children].map(child=>({node:child,links:child.matches('a')?[child]:[...child.querySelectorAll('a')]}))}));
try{nav.classList.toggle('tc-collapsed',sessionStorage.getItem('tc-review-tcs-collapsed')==='true')}catch{}
function updateNodeToggle(){const collapsed=nav.classList.contains('tc-collapsed');nodeToggle.textContent=collapsed?'\ub178\ub4dc\ub9cc \ud3bc\uce58\uae30':'\ub178\ub4dc\ub9cc \uc811\uae30';nodeToggle.title=collapsed?'Expand TC nodes':'Collapse TC nodes'}
function updateAllToggle(){const expanded=branches.every(branch=>branch.node.open);allToggle.textContent=expanded?'\ubaa8\ub450 \uc811\uae30':'\ubaa8\ub450 \ud3bc\uce58\uae30';allToggle.title=expanded?'Collapse all suites to version level':'Expand all suites'}
updateNodeToggle();updateAllToggle();
try{const saved=JSON.parse(sessionStorage.getItem('tc-review-tree-open')||'{}');branches.forEach(({node})=>{const state=saved[node.dataset.node];if(state!==undefined){node.open=typeof state==='object'?state.open:state;if(typeof state==='object'&&state.showTcs)node.dataset.showTcs='true'}})}catch{}
function saveTreeState(){try{sessionStorage.setItem('tc-review-tree-open',JSON.stringify(Object.fromEntries(branches.map(({node})=>[node.dataset.node,{open:node.open,showTcs:node.dataset.showTcs==='true'}]))))}catch{}}
branches.forEach(({node})=>{
 node.addEventListener('toggle',()=>{if(!search.value.trim())saveTreeState();updateAllToggle()});
 node.querySelector(':scope > summary').addEventListener('click',event=>{
  if(!nav.classList.contains('tc-collapsed')||!node.querySelector(':scope > .tree-children > a'))return;
  event.preventDefault();node.dataset.showTcs=node.dataset.showTcs==='true'?'false':'true';node.open=true;saveTreeState();
 });
});
function highlight(target,terms){
 if(!terms.length){target.node.textContent=target.text;return}
 const chars=Array.from(target.text),folded=[],mapping=[],marked=new Set();
 chars.forEach((char,index)=>Array.from(char.normalize('NFKC').toLowerCase()).forEach(letter=>{folded.push(letter);mapping.push(index)}));
 for(const term of terms){let cursor=0,positions=[];for(const letter of term){const index=folded.indexOf(letter,cursor);if(index<0){positions=[];break}positions.push(mapping[index]);cursor=index+1}positions.forEach(index=>marked.add(index))}
 if(!marked.size){target.node.textContent=target.text;return}
 const fragment=document.createDocumentFragment();let buffer='',last=false;
 function flush(){if(!buffer)return;const part=last?document.createElement('mark'):document.createTextNode('');part.textContent=buffer;fragment.append(part);buffer=''}
 chars.forEach((char,index)=>{const active=marked.has(index);if(active!==last){flush();last=active}buffer+=char});flush();target.node.replaceChildren(fragment)
}
function bestGroupScore(record,groups){
 let overall=null;
 for(const group of groups){
  let score=0,matched=true;
  for(const term of group){
   const value=termScore(term,record.fields);
   if(term.exclude){if(value!==null){matched=false;break}continue}
   if(value===null){matched=false;break}
   score+=value;if(record.title.includes(term.value))score+=100;
  }
  if(matched&&(overall===null||score>overall))overall=score;
 }
 return overall;
}
const searchTerms=query=>query.flat().filter(term=>!term.exclude).map(term=>term.value);
let matches=[],selected=0,searching=false,previousOpen=new Map(),previousHighlighted=new Set(),lastOrder=[],activeLink=null;
function selectResult(index){
 if(activeLink)activeLink.removeAttribute('aria-current');
 selected=Math.max(0,Math.min(index,Math.max(0,matches.length-1)));
 activeLink=matches.length?matches[selected].link:null;
 if(matches.length){activeLink?.setAttribute('aria-current','true');let parent=activeLink?.parentElement;while(parent){if(parent.tagName==='DETAILS')parent.open=true;parent=parent.parentElement}}
}
function filter(){
 const started=performance.now(),groups=parseQuery(search.value),active=matches[selected]?.id;
 if(groups.length&&!searching)previousOpen=new Map(branches.map(({node})=>[node,node.open]));
 matches=[];
 for(const record of cardsData){
  const score=groups.length?bestGroupScore(record,groups):0,show=score!==null;
  if(record.card.hidden===show)record.card.hidden=!show;
  if(record.link&&record.link.hidden===show)record.link.hidden=!show;
  if(show)matches.push({...record,score});
 }
 matches.sort((a,b)=>b.score-a.score||a.index-b.index);
 const ordered=groups.length?[...matches,...cardsData.filter(record=>record.card.hidden)]:cardsData;
 if(ordered.length!==lastOrder.length||ordered.some((record,index)=>record.card!==lastOrder[index])){
  const fragment=document.createDocumentFragment();ordered.forEach(record=>fragment.append(record.card));results.append(fragment);lastOrder=ordered.map(record=>record.card)
 }
 const scoreByLink=new Map(matches.map(record=>[record.link,record.score]));
 for(const {node,children} of containers){
  const ranked=groups.length?children.map((entry,index)=>({entry,index,score:entry.links.reduce((best,link)=>Math.max(best,scoreByLink.get(link)??-Infinity),-Infinity)})).sort((a,b)=>b.score-a.score||a.index-b.index).map(item=>item.entry):children;
  if(ranked.some((entry,index)=>entry.node!==children[index].node))node.append(...ranked.map(entry=>entry.node))
 }
 const branchCounts=new Map(branches.map(({node})=>[node,0]));
 for(const record of matches){let parent=record.link?.parentElement;while(parent&&parent!==nav){if(parent.tagName==='DETAILS')branchCounts.set(parent,(branchCounts.get(parent)||0)+1);parent=parent.parentElement}}
 for(const {node,total} of branches){
  const count=branchCounts.get(node)||0;
  node.hidden=count===0;
  node.querySelector(':scope > summary .tree-count').textContent=total+'\uac1c';
  if(groups.length&&count)node.open=true;
  else if(!groups.length&&searching)node.open=previousOpen.get(node)??node.open;
 }
 const positive=searchTerms(groups),touched=new Set([...previousHighlighted,...matches]);
 for(const record of touched){
  const terms=record.card.hidden?[]:positive;
  record.targets.forEach(target=>highlight(target,terms));
  record.navTargets.forEach(target=>highlight(target,terms));
 }
 branchLabels.forEach(target=>highlight(target,positive));
 previousHighlighted=new Set(matches);
 document.getElementById('count').textContent=matches.length+' / '+cards.length+' TC';
 document.getElementById('empty').hidden=matches.length>0;
 searching=groups.length>0;
 const hash=decodeURIComponent(location.hash.slice(1)),preferred=matches.findIndex(record=>record.id===(hash||active));
 selectResult(preferred<0?0:preferred);
 search.dataset.filterMs=(performance.now()-started).toFixed(1);
}
function clearTreeSearch(){if(search.value.trim()){search.value='';filter()}}
nodeToggle.addEventListener('click',()=>{clearTreeSearch();branches.forEach(({node})=>{node.open=true;delete node.dataset.showTcs});const collapsed=!nav.classList.contains('tc-collapsed');nav.classList.toggle('tc-collapsed',collapsed);updateNodeToggle();updateAllToggle();try{sessionStorage.setItem('tc-review-tcs-collapsed',String(collapsed))}catch{}saveTreeState()});
allToggle.addEventListener('click',()=>{clearTreeSearch();const collapse=branches.every(({node})=>node.open);branches.forEach(({node})=>{node.open=!collapse||node.dataset.node==='/HPE990';delete node.dataset.showTcs});nav.classList.remove('tc-collapsed');updateNodeToggle();updateAllToggle();try{sessionStorage.setItem('tc-review-tcs-collapsed','false')}catch{}saveTreeState()});
cardsData.forEach(record=>record.link?.addEventListener('click',()=>{const index=matches.findIndex(item=>item.id===record.id);if(index>=0)selectResult(index)}));
window.addEventListener('hashchange',()=>{const index=matches.findIndex(record=>record.id===decodeURIComponent(location.hash.slice(1)));if(index>=0)selectResult(index)});
let composing=false,filterTimer=null;
function scheduleFilter(delay=10){clearTimeout(filterTimer);filterTimer=setTimeout(filter,delay)}
search.addEventListener('compositionstart',()=>{composing=true;clearTimeout(filterTimer)});
search.addEventListener('compositionend',()=>{composing=false;scheduleFilter(0)});
search.addEventListener('input',()=>{if(!composing)scheduleFilter()});
search.addEventListener('keydown',event=>{
 if(event.isComposing||composing)return;
 if(event.key==='ArrowDown'||event.key==='ArrowUp'){event.preventDefault();selectResult(selected+(event.key==='ArrowDown'?1:-1));if(matches.length)matches[selected].link?.scrollIntoView({block:'nearest'})}
 else if(event.key==='Enter'&&matches.length){event.preventDefault();matches[selected].link?.click()}
});
filter();
