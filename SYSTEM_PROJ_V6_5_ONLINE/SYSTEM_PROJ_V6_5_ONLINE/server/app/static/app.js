const API='/api/v1'; let token=sessionStorage.getItem('access_token'); let refreshToken=localStorage.getItem('refresh_token'); let me=null; let ws=null; let currentView='dashboard';

function isAdminRole(role){return ['ADMIN','MASTER_ADMIN'].includes(role)}
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
async function api(path,opts={}){opts.headers=opts.headers||{}; if(token)opts.headers.Authorization=`Bearer ${token}`; if(opts.json){opts.headers['Content-Type']='application/json';opts.body=JSON.stringify(opts.json);delete opts.json} let r=await fetch(API+path,opts); if(r.status===401&&refreshToken){let rr=await fetch(API+'/auth/refresh',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({refresh_token:refreshToken})});if(rr.ok){let d=await rr.json();token=d.access_token;sessionStorage.setItem('access_token',token);opts.headers.Authorization=`Bearer ${token}`;r=await fetch(API+path,opts)}} if(!r.ok){let e={};try{e=await r.json()}catch{} throw new Error(e.detail||`Erro ${r.status}`)} let ct=r.headers.get('content-type')||'';return ct.includes('json')?r.json():r.blob()}
function authTab(name){$$('.tab').forEach(x=>x.classList.toggle('active',x.dataset.auth===name));$('#loginForm').classList.toggle('hidden',name!=='login');$('#registerForm').classList.toggle('hidden',name!=='register');$('#migratedForm').classList.toggle('hidden',name!=='migrated');$('#authMsg').textContent=''}
$$('.tab').forEach(b=>b.onclick=()=>authTab(b.dataset.auth));
$('#loginForm').onsubmit=async e=>{e.preventDefault();let f=new FormData(e.target);try{let d=await api('/auth/login',{method:'POST',json:{login:f.get('login'),password:f.get('password'),device_name:`Web ${navigator.platform}`}});token=d.access_token;refreshToken=d.refresh_token;sessionStorage.setItem('access_token',token);localStorage.setItem('refresh_token',refreshToken);await boot()}catch(err){$('#authMsg').textContent=err.message}};
$('#registerForm').onsubmit=async e=>{e.preventDefault();let f=new FormData(e.target);if(f.get('password')!==f.get('confirm'))return $('#authMsg').textContent='As senhas não conferem.';try{let d=await api('/auth/register',{method:'POST',json:{full_name:f.get('full_name'),email:f.get('email'),username:f.get('username'),badge:f.get('badge'),password:f.get('password')}});$('#authMsg').textContent=d.message;authTab('login')}catch(err){$('#authMsg').textContent=err.message}};
$('#migratedForm').onsubmit=async e=>{e.preventDefault();let f=new FormData(e.target);if(f.get('password')!==f.get('confirm'))return $('#authMsg').textContent='As senhas não conferem.';try{let d=await api('/auth/claim-migrated',{method:'POST',json:{username:f.get('username'),activation_code:f.get('activation_code'),full_name:f.get('full_name'),email:f.get('email'),badge:f.get('badge'),password:f.get('password')}});$('#authMsg').textContent=d.message;authTab('login')}catch(err){$('#authMsg').textContent=err.message}};
$('#forgot').onclick=async e=>{e.preventDefault();let email=prompt('Informe seu e-mail cadastrado:');if(email){await api('/auth/request-password-reset',{method:'POST',json:{email}});alert('Se o e-mail existir, as instruções serão enviadas.')}};
$('#logout').onclick=()=>{sessionStorage.clear();localStorage.removeItem('refresh_token');location.reload()};$('#refresh').onclick=()=>render(currentView);$('#closeModal').onclick=()=>$('#modal').classList.add('hidden');
$$('.nav').forEach(b=>b.onclick=()=>{currentView=b.dataset.view;$$('.nav').forEach(x=>x.classList.toggle('active',x===b));render(currentView)});
async function boot(){try{me=await api('/auth/me');$('#auth').classList.add('hidden');$('#app').classList.remove('hidden');$('#userName').textContent=me.full_name;$('#userRole').textContent=me.role==='MASTER_ADMIN'?'MASTER ADMIN':me.role;$$('.admin-only').forEach(x=>x.style.display=isAdminRole(me.role)?'':'none');connectWs();if('Notification' in window&&Notification.permission==='default')Notification.requestPermission();render('dashboard');setInterval(()=>api('/sessions/ping',{method:'POST'}).catch(()=>{}),30000)}catch{sessionStorage.clear();$('#auth').classList.remove('hidden')}}
function connectWs(){if(ws)ws.close();let proto=location.protocol==='https:'?'wss':'ws';ws=new WebSocket(`${proto}://${location.host}${API}/ws?token=${encodeURIComponent(token)}`);ws.onmessage=e=>{let d=JSON.parse(e.data);if(d.type==='notification'){loadNotifBadge();if('Notification' in window&&Notification.permission==='granted')new Notification(d.notification.title,{body:d.notification.message});else console.info(d.notification.title,d.notification.message);if(currentView==='notifications')render('notifications')}if(d.type==='project_update'&&['dashboard','projects'].includes(currentView))render(currentView)}}
async function loadNotifBadge(){try{let n=await api('/notifications');let c=n.filter(x=>!x.read).length;$('#notifBadge').textContent=c?`(${c})`:''}catch{}}
async function render(view){currentView=view;let titles={dashboard:['Project Center','Acompanhe projetos abertos e pendências'],projects:['Projetos','Todos os projetos ativos em um só lugar'],notifications:['Notificações','Solicitações e avisos do sistema'],materials:['Banco de insumos','Catálogo central usado nas transferências'],admin:['Administração','Usuários, sessões e auditoria']};$('#viewTitle').textContent=titles[view][0];$('#viewSubtitle').textContent=titles[view][1];if(view==='dashboard')return dashboard();if(view==='projects')return projects();if(view==='notifications')return notifications();if(view==='materials')return materials();if(view==='admin')return admin()}
async function dashboard(){
  let d=await api('/projects?page_size=100');
  let p=d.items;

  let pendingTransfer=p.filter(x=>!x.transfer_requested).length;
  let inLogistics=p.filter(
    x=>x.transport_stage!=='AGUARDANDO PROGRAMAÇÃO DE TRANSPORTE'
       && x.transport_stage!=='EQUIPAMENTOS ENVIADOS'
  ).length;
  let myProjects=p.filter(
    x=>x.current_responsible?.id===me.id
  ).length;

  let metrics=[
    ['Projetos abertos',p.length],
    ['Pendentes de transferência',pendingTransfer],
    ['Em logística',inLogistics],
    ['Sob minha responsabilidade',myProjects]
  ];

  $('#content').innerHTML=`
    <div class="cards">
      ${metrics.map(x=>`
        <div class="card metric">
          <div class="label">${x[0]}</div>
          <div class="value">${x[1]}</div>
        </div>
      `).join('')}
    </div>

    <div class="section-title-row">
      <div>
        <h3>Projetos recentes</h3>
        <div class="muted">Acesso rápido aos últimos projetos ativos</div>
      </div>
      <button class="primary" id="dashboardNewProject">Novo projeto</button>
    </div>

    <div id="recent">
      ${p.length
        ? p.slice(0,10).map(projectCard).join('')
        : `<div class="empty-state">
             Nenhum projeto aberto. Crie o primeiro projeto para iniciar o acompanhamento.
           </div>`
      }
    </div>
  `;

  $('#dashboardNewProject').onclick=()=>newProjectModal();
  loadNotifBadge();
}

function projectStatusClass(p){
  if(
    p.transport_stage==='EQUIPAMENTOS ENVIADOS'
    || p.container_status==='CONTAINER ENVIADO'
  ) return 'done';

  if(
    p.transport_stage!=='AGUARDANDO PROGRAMAÇÃO DE TRANSPORTE'
    || p.container_status==='CONTAINER LOCADO'
    || p.container_status==='CONTAINER SENDO CARREGADO'
  ) return 'logistics';

  return 'pending';
}

function projectCard(p){
  let cls=projectStatusClass(p);
  let transfer=p.transfer_requested?'Transferência solicitada':'Transferência pendente';

  return `
    <div class="card project-card status-${cls}">
      <div class="osbox">OS ${p.os}</div>
      <div>
        <h3>${p.title}</h3>
        <div class="meta">
          ${p.client}
          • Responsável: ${p.current_responsible?.full_name||'-'}
          • ${transfer}
        </div>
      </div>
      <div>
        <span class="pill ${cls}">${p.status}</span>
      </div>
      <button onclick="openProject(${p.id})">Abrir</button>
    </div>
  `;
}
async function projects(){let d=await api('/projects?page_size=100');$('#content').innerHTML=`<div class="toolbar"><input id="pq" placeholder="Buscar OS, cliente ou projeto"><button id="psearch">Buscar</button><button id="newProject">Novo projeto</button></div><div id="plist">${d.items.map(projectCard).join('')}</div>`;$('#psearch').onclick=async()=>{let q=$('#pq').value;let r=await api('/projects?page_size=100&q='+encodeURIComponent(q));$('#plist').innerHTML=r.items.map(projectCard).join('')};$('#newProject').onclick=()=>newProjectModal()}
function newProjectModal(){showModal(`<h2>Novo projeto</h2><form id="np" class="form"><input name="os" placeholder="OS" required><input name="client" placeholder="Cliente" required><input name="title" placeholder="Projeto" required><label>Lista de consumíveis Word (opcional)</label><input name="file" type="file" accept=".docx"><button>Criar projeto</button></form>`);$('#np').onsubmit=async e=>{e.preventDefault();let f=new FormData(e.target);try{if(f.get('file')&&f.get('file').size){let fd=new FormData();fd.append('os_value',f.get('os'));fd.append('client',f.get('client'));fd.append('title',f.get('title'));fd.append('file',f.get('file'));let r=await fetch(API+'/projects/from-word',{method:'POST',headers:{Authorization:`Bearer ${token}`},body:fd});if(!r.ok)throw new Error((await r.json()).detail||'Erro');}else await api('/projects',{method:'POST',json:{os:f.get('os'),client:f.get('client'),title:f.get('title')}});closeModal();render('projects')}catch(err){alert(err.message)}}}
async function openProject(id){
  let p=await api(`/projects/${id}`);
  let ts=await api(`/projects/${id}/transfer/status`);
  let events=p.stage_events.map(e=>`<div class="event"><strong>${e.stage}</strong><br><span class="muted">${new Date(e.occurred_at).toLocaleString('pt-BR')}</span></div>`).join('');
  let hist=p.responsibility_history.map(h=>`<tr><td>${h.full_name}</td><td>${new Date(h.started_at).toLocaleString('pt-BR')}</td><td>${h.ended_at?new Date(h.ended_at).toLocaleString('pt-BR'):'Atual'}</td><td>${h.reason||''}</td></tr>`).join('');

  showModal(`
    <h2>OS ${p.os} — ${p.title}</h2>
    <p>${p.client}</p>

    <div class="cards">
      <div class="card"><b>Iniciado por</b><p>${p.initiated_by?.full_name||'-'}</p></div>
      <div class="card"><b>Responsável atual</b><p>${p.current_responsible?.full_name||'-'}</p></div>
      <div class="card"><b>Container</b><p>${p.container_status}</p></div>
      <div class="card"><b>Transporte</b><p>${p.transport_stage}</p></div>
    </div>

    <div class="section">
      <h3>Solicitação de transferência de consumíveis</h3>
      <div class="cards">
        <div class="card"><b>Status</b><p>${ts.status}</p></div>
        <div class="card"><b>Transferíveis</b><p>${ts.transferable}</p></div>
        <div class="card"><b>Revisão / fora da transferência</b><p>${ts.review}</p></div>
      </div>
      ${ts.sent_at?`<p><b>Enviada em:</b> ${new Date(ts.sent_at).toLocaleString('pt-BR')}</p>`:''}
      ${ts.generated_at&&!ts.sent_at?`<p><b>Planilha gerada em:</b> ${new Date(ts.generated_at).toLocaleString('pt-BR')}</p>`:''}
      ${p.can_edit?`
        <button id="prepareTransferWeb" class="primary">GERAR SOLICITAÇÃO</button>
        ${ts.latest_document&&!ts.sent?`<button id="confirmTransferWeb" class="success">CONFIRMAR QUE ENVIEI</button>`:''}
        <p class="muted">
          No navegador a planilha será baixada. Para abrir o Outlook já com
          anexo e assinatura automaticamente, use o Project Center Desktop no
          computador onde está o Outlook.
        </p>
      `:''}
    </div>

    ${p.can_edit?`
      <div class="section">
        <h3>Logística</h3>
        <form id="flow" class="form grid2">
          <input name="collection_forecast" value="${p.collection_forecast||''}" placeholder="Previsão coleta">
          <label><input type="checkbox" name="consumables_collected" ${p.consumables_collected?'checked':''}> Consumíveis coletados</label>
          <select name="container_status">${['AGUARDANDO DEFINIÇÃO DO CONTAINER','CONTAINER LOCADO','CONTAINER SENDO CARREGADO','CONTAINER ENVIADO','PROJETO SEM CONTAINER'].map(x=>`<option ${x===p.container_status?'selected':''}>${x}</option>`).join('')}</select>
          <select name="transport_stage">${['AGUARDANDO PROGRAMAÇÃO DE TRANSPORTE','PROGRAMAÇÃO DE TRANSPORTE ALINHADA','CARREGANDO EQUIPAMENTOS NO CAMINHÃO','EQUIPAMENTOS ENVIADOS'].map(x=>`<option ${x===p.transport_stage?'selected':''}>${x}</option>`).join('')}</select>
          <button class="primary">Salvar logística</button>
        </form>
      </div>

      <div class="section">
        <button id="transferResp" class="primary">Transferir responsabilidade do projeto</button>
      </div>
    `:''}

    <div class="section">
      <h3>Linha do tempo</h3>
      <div class="timeline">${events||'Sem eventos'}</div>
    </div>

    <div class="section">
      <h3>Histórico de responsáveis</h3>
      <div class="table-wrap">
        <table>
          <tr><th>Responsável</th><th>Início</th><th>Fim</th><th>Motivo</th></tr>
          ${hist}
        </table>
      </div>
    </div>

    <div class="section">
      <h3>Romaneio</h3>
      <button onclick="downloadFile('/projects/${id}/romaneio.xlsx','romaneio.xlsx')">Gerar XLSX</button>
      <button onclick="downloadFile('/projects/${id}/romaneio.pdf','romaneio.pdf')">Gerar PDF</button>
    </div>
  `);

  if(p.can_edit){
    $('#flow').onsubmit=async e=>{
      e.preventDefault();
      let f=new FormData(e.target);
      try{
        await api(`/projects/${id}/flow`,{
          method:'PUT',
          json:{
            version:p.version,
            transfer_requested:null,
            collection_forecast:f.get('collection_forecast'),
            consumables_collected:!!f.get('consumables_collected'),
            container_status:f.get('container_status'),
            transport_stage:f.get('transport_stage')
          }
        });
        closeModal();
        openProject(id);
      }catch(err){
        alert(err.message);
      }
    };

    $('#transferResp').onclick=()=>transferResponsibility(id);

    $('#prepareTransferWeb').onclick=async()=>{
      try{
        let prep=await api(`/projects/${id}/transfer/prepare`,{method:'POST'});
        await downloadFile(`/documents/${prep.document_id}/download`,prep.filename);

        let to=prep.recipients.join(';');
        let mailto=`mailto:${encodeURIComponent(to)}?subject=${encodeURIComponent(prep.subject)}&body=${encodeURIComponent(prep.body_text)}`;

        alert(
          'A planilha foi gerada e baixada.\\n\\n'
          +'O navegador abrirá o cliente de e-mail com destinatários e corpo. '
          +'Por segurança do navegador, o anexo precisa ser incluído manualmente.\\n\\n'
          +'No Desktop do Project Center o anexo e a assinatura são tratados automaticamente.'
        );

        window.location.href=mailto;
        closeModal();
        openProject(id);
      }catch(err){
        alert(err.message);
      }
    };

    let confirmButton=$('#confirmTransferWeb');
    if(confirmButton){
      confirmButton.onclick=async()=>{
        if(!confirm('Confirme somente se o e-mail foi realmente enviado. Marcar como enviado?'))return;
        try{
          await api(`/projects/${id}/transfer/confirm-sent`,{method:'POST'});
          closeModal();
          openProject(id);
        }catch(err){
          alert(err.message);
        }
      };
    }
  }
}
async function transferResponsibility(projectId){let users=await api('/users/active');showModal(`<h2>Transferir responsabilidade</h2><form id="tr" class="form"><select name="to_user_id">${users.filter(x=>x.id!==me.id).map(x=>`<option value="${x.id}">${x.full_name}</option>`).join('')}</select><textarea name="reason" placeholder="Motivo (ex.: férias)" required></textarea><button>Enviar solicitação</button></form>`);$('#tr').onsubmit=async e=>{e.preventDefault();let f=new FormData(e.target);try{await api(`/projects/${projectId}/responsibility/request`,{method:'POST',json:{to_user_id:+f.get('to_user_id'),reason:f.get('reason')}});alert('Solicitação enviada. O novo responsável receberá uma notificação.');closeModal()}catch(err){alert(err.message)}}}
async function notifications(){let n=await api('/notifications');let inbox=await api('/responsibility-transfers/inbox');$('#content').innerHTML=`<div class="section"><h3>Transferências aguardando sua decisão</h3>${inbox.map(x=>`<div class="card"><b>OS ${x.os} — ${x.title}</b><p>${x.from_user}: ${x.reason}</p><button class="success" onclick="decide(${x.id},true)">Aceitar</button> <button class="danger" onclick="decide(${x.id},false)">Recusar</button></div>`).join('')||'<p>Nenhuma.</p>'}</div><div class="section"><h3>Notificações</h3>${n.map(x=>`<div class="card notification ${x.read?'':'unread'}"><div><b>${x.title}</b><p>${x.message}</p><small>${new Date(x.created_at).toLocaleString('pt-BR')}</small></div>${x.read?'':`<button onclick="readNotif(${x.id})">Marcar lida</button>`}</div>`).join('')}</div>`;loadNotifBadge()}
async function decide(id,accept){await api(`/responsibility-transfers/${id}/decision`,{method:'POST',json:{accept}});render('notifications')};async function readNotif(id){await api(`/notifications/${id}/read`,{method:'POST'});render('notifications')}
async function materials(){
  let d=await api('/materials?page_size=100');

  $('#content').innerHTML=`
    ${isAdminRole(me.role)?`
      <div class="import-panel">
        <h3>Importar banco de insumos</h3>
        <div class="muted">
          Aceita .xlsx e .xlsm. O arquivo pode usar a planilha CONSULTA com
          Material, Texto breve de material, Centro, Depósito e UM básica.
        </div>

        <div class="import-actions">
          <input id="mfile" type="file" accept=".xlsx,.xlsm">
          <label>
            <input id="mreplace" type="checkbox">
            Desativar insumos antigos que não estiverem no novo arquivo
          </label>
          <button id="mimport" class="primary">Importar catálogo</button>
          <div class="catalog-summary">
            <strong>${d.total}</strong> registros no banco
          </div>
        </div>

        <div id="mimportStatus" class="import-status">
          Selecione o Excel do catálogo para iniciar.
        </div>
      </div>
    `:''}

    <div class="toolbar">
      <input id="mq" placeholder="Buscar código ou descrição">
      <button id="msearch">Buscar</button>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Código</th>
            <th>Descrição</th>
            <th>Centro</th>
            <th>Depósito</th>
            <th>UM</th>
            <th>Ativo</th>
          </tr>
        </thead>
        <tbody id="mtbody">
          ${d.items.map(materialRow).join('')}
        </tbody>
      </table>
    </div>
  `;

  $('#msearch').onclick=async()=>{
    let r=await api(
      '/materials?page_size=100&q='+
      encodeURIComponent($('#mq').value)
    );

    $('#mtbody').innerHTML=r.items.map(materialRow).join('');
  };

  if(isAdminRole(me.role)){
    $('#mimport').onclick=async()=>{
      let input=$('#mfile');
      let file=input.files[0];
      let status=$('#mimportStatus');
      let button=$('#mimport');

      if(!file){
        status.className='import-status error';
        status.textContent='Selecione um arquivo .xlsx ou .xlsm.';
        return;
      }

      button.disabled=true;
      button.textContent='Importando...';
      status.className='import-status';
      status.textContent=
        `Enviando ${file.name} (${Math.ceil(file.size/1024)} KB). `+
        'Aguarde; o primeiro carregamento no Render gratuito pode demorar.';

      let fd=new FormData();
      fd.append('file',file);
      fd.append(
        'replace',
        $('#mreplace').checked?'true':'false'
      );

      try{
        let r=await fetch(
          API+'/materials/import',
          {
            method:'POST',
            headers:{
              Authorization:`Bearer ${token}`
            },
            body:fd
          }
        );

        let result={};

        try{
          result=await r.json();
        }catch{}

        if(!r.ok){
          throw new Error(
            result.detail || `Erro HTTP ${r.status}`
          );
        }

        status.className='import-status ok';
        status.innerHTML=
          `<strong>Importação concluída.</strong> `+
          `${result.processed} processados • `+
          `${result.created} novos • `+
          `${result.updated} atualizados • `+
          `${result.ignored} ignorados • `+
          `${result.active_total} ativos • `+
          `${result.elapsed_seconds}s`;

        setTimeout(
          ()=>render('materials'),
          1800
        );

      }catch(err){
        status.className='import-status error';
        status.textContent=
          'Falha ao importar: '+err.message;
      }finally{
        button.disabled=false;
        button.textContent='Importar catálogo';
      }
    };
  }
}

function materialRow(x){
  return `
    <tr>
      <td><strong>${x.code}</strong></td>
      <td>${x.description}</td>
      <td>${x.center}</td>
      <td>${x.deposit}</td>
      <td>${x.unit}</td>
      <td>${x.active?'SIM':'NÃO'}</td>
    </tr>
  `;
}

async function admin(){if(!isAdminRole(me.role))return;let users=await api('/admin/users');let online=await api('/admin/online-users');let act=await api('/admin/activity?limit=50');$('#content').innerHTML=`<div class="cards"><div class="card metric"><div class="label">Usuários pendentes</div><div class="value">${users.filter(x=>x.status==='PENDING').length}</div></div><div class="card metric"><div class="label">Online agora</div><div class="value">${online.length}</div></div></div><div class="section"><h3>Usuários</h3><div class="table-wrap"><table><tr><th>Nome</th><th>E-mail</th><th>Crachá</th><th>Perfil</th><th>Status</th><th>Ação</th></tr>${users.map(x=>`<tr><td>${x.full_name}</td><td>${x.email}</td><td>${x.badge}</td><td>${x.role}</td><td>${x.status}</td><td>${x.status==='PENDING'?`<button onclick="approveUser(${x.id})">Aprovar</button>`:''}</td></tr>`).join('')}</table></div></div><div class="section"><h3>Atividade recente</h3><div class="table-wrap"><table><tr><th>Quando</th><th>Usuário</th><th>Ação</th><th>Entidade</th></tr>${act.map(x=>`<tr><td>${new Date(x.created_at).toLocaleString('pt-BR')}</td><td>${x.actor}</td><td>${x.action}</td><td>${x.entity_type} ${x.entity_id}</td></tr>`).join('')}</table></div></div>`}
async function approveUser(id){let allowed=me.role==='MASTER_ADMIN'?'OPERATOR, CONSULTA ou ADMIN':'OPERATOR ou CONSULTA';let role=prompt(`Perfil: ${allowed}`,'OPERATOR');if(role){try{await api(`/admin/users/${id}/approve`,{method:'POST',json:{role}});render('admin')}catch(err){alert(err.message)}}}
async function downloadFile(path,name){let b=await api(path);let a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}
function showModal(html){$('#modalBody').innerHTML=html;$('#modal').classList.remove('hidden')}function closeModal(){$('#modal').classList.add('hidden')}
$('#globalSearch').onkeydown=async e=>{if(e.key==='Enter'){let q=e.target.value;if(q.length<2)return;let r=await api('/search?q='+encodeURIComponent(q));showModal(`<h2>Resultados para “${q}”</h2><h3>Projetos</h3>${r.projects.map(projectCard).join('')||'<p>Nenhum</p>'}<h3>Materiais</h3>${r.materials.map(x=>`<p><b>${x.code}</b> — ${x.description}</p>`).join('')||'<p>Nenhum</p>'}<h3>Usuários</h3>${r.users.map(x=>`<p>${x.full_name} — ${x.email}</p>`).join('')||'<p>Nenhum</p>'}`)}};
if(token)boot();
