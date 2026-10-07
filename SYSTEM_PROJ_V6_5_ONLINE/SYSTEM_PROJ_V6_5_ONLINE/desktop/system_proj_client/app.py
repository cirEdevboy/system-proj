from __future__ import annotations
import json, os, sys, tempfile, threading, time
from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
 QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QFormLayout,QLineEdit,QPushButton,QLabel,QStackedWidget,QListWidget,QListWidgetItem,QTableWidget,QTableWidgetItem,QHeaderView,QDialog,QTabWidget,QComboBox,QCheckBox,QMessageBox,QFileDialog,QTextEdit,QSpinBox,QDoubleSpinBox,QAbstractItemView,QSystemTrayIcon,QStyle,QInputDialog
)
import websocket
from .api import ApiClient
from .outlook import selected_email_word, open_transfer_draft

BLUE="#003B7A"; BLUE2="#0050A4"; BG="#EEF2F6"; CARD="#FFFFFF"; MUTED="#667085"
STYLE=f"""QWidget{{font-family:'Segoe UI';font-size:10pt;color:#17202A}}QMainWindow{{background:{BG}}}QPushButton{{background:{BLUE2};color:white;border:0;border-radius:7px;padding:8px 12px}}QPushButton:hover{{background:{BLUE}}}QLineEdit,QComboBox,QTextEdit,QDoubleSpinBox{{background:white;border:1px solid #CBD5E1;border-radius:7px;padding:7px}}QTableWidget{{background:white;border:1px solid #E2E8F0;border-radius:8px;gridline-color:#E2E8F0}}QHeaderView::section{{background:#F8FAFC;border:0;border-bottom:1px solid #E2E8F0;padding:8px;font-weight:600}}"""

def _is_admin_role(role):
    return role in ("ADMIN", "MASTER_ADMIN")


class WsThread(QThread):
    event=Signal(dict)
    def __init__(self,api):super().__init__();self.api=api;self._stop=False
    def run(self):
        while not self._stop:
            try:
                ws=websocket.create_connection(self.api.websocket_url,timeout=20)
                while not self._stop:
                    msg=ws.recv();self.event.emit(json.loads(msg))
            except Exception: time.sleep(4)
    def stop(self):self._stop=True

class LoginWindow(QWidget):
    logged=Signal()
    def __init__(self,api):
        super().__init__();self.api=api;self.setWindowTitle("Project Center | Acesso");self.resize(480,520);v=QVBoxLayout(self);title=QLabel("PROJECT CENTER");title.setStyleSheet(f"font-size:28px;font-weight:900;color:{BLUE2}");v.addWidget(title);v.addWidget(QLabel("Gestão de projetos e logística — ambiente online"));self.tabs=QTabWidget();v.addWidget(self.tabs)
        login=QWidget();f=QFormLayout(login);self.login=QLineEdit();self.password=QLineEdit();self.password.setEchoMode(QLineEdit.Password);btn=QPushButton("Entrar");btn.clicked.connect(self.do_login);f.addRow("Usuário/e-mail/crachá",self.login);f.addRow("Senha",self.password);f.addRow(btn);self.tabs.addTab(login,"Entrar")
        reg=QWidget();rf=QFormLayout(reg);self.rname=QLineEdit();self.remail=QLineEdit();self.ruser=QLineEdit();self.rbadge=QLineEdit();self.rpass=QLineEdit();self.rpass.setEchoMode(QLineEdit.Password);rb=QPushButton("Cadastrar");rb.clicked.connect(self.do_register)
        for label,w in [("Nome completo",self.rname),("E-mail",self.remail),("Usuário",self.ruser),("Crachá",self.rbadge),("Senha (mín. 8)",self.rpass)]:rf.addRow(label,w)
        rf.addRow(rb);self.tabs.addTab(reg,"Primeiro acesso")

        mig=QWidget();mf=QFormLayout(mig)
        self.muser=QLineEdit()
        self.mcode=QLineEdit()
        self.mname=QLineEdit()
        self.memail=QLineEdit()
        self.mbadge=QLineEdit()
        self.mpass=QLineEdit()
        self.mpass.setEchoMode(QLineEdit.Password)
        mb=QPushButton("Ativar conta migrada")
        mb.clicked.connect(self.do_claim_migrated)
        for label,w in [
            ("Usuário da V5",self.muser),
            ("Código de ativação",self.mcode),
            ("Nome completo",self.mname),
            ("E-mail",self.memail),
            ("Crachá",self.mbadge),
            ("Nova senha (mín. 8)",self.mpass),
        ]:mf.addRow(label,w)
        mf.addRow(mb)
        self.tabs.addTab(mig,"Conta migrada")

        self.server_info=QLabel()
        self.server_info.setWordWrap(True)
        self.update_server_info()
        v.addWidget(self.server_info)

        server=QPushButton("Configurar servidor")
        server.clicked.connect(self.server_config)
        v.addWidget(server)

        test_server=QPushButton("Testar conexão")
        test_server.clicked.connect(self.test_server)
        v.addWidget(test_server)

        self.msg=QLabel()
        self.msg.setWordWrap(True)
        self.msg.setStyleSheet("color:#DC2626")
        v.addWidget(self.msg)
    def do_login(self):
        try:self.api.login(self.login.text(),self.password.text());self.logged.emit()
        except Exception as e:self.msg.setText(str(e))
    def do_register(self):
        try:d=self.api.register({"full_name":self.rname.text(),"email":self.remail.text(),"username":self.ruser.text(),"badge":self.rbadge.text(),"password":self.rpass.text()});QMessageBox.information(self,"Cadastro",d["message"]);self.tabs.setCurrentIndex(0)
        except Exception as e:self.msg.setText(str(e))
    def do_claim_migrated(self):
        try:
            d=self.api.claim_migrated({
                "username":self.muser.text(),
                "activation_code":self.mcode.text(),
                "full_name":self.mname.text(),
                "email":self.memail.text(),
                "badge":self.mbadge.text(),
                "password":self.mpass.text(),
            })
            QMessageBox.information(
                self,
                "Conta migrada",
                d["message"]
            )
            self.tabs.setCurrentIndex(0)
        except Exception as e:
            self.msg.setText(str(e))

    def update_server_info(self):
        url=self.api.config.get("server_url","http://localhost:8000")
        self.server_info.setText(
            f"Servidor configurado: {url}"
        )

    def test_server(self):
        try:
            data=self.api.health()
            self.msg.setStyleSheet("color:#15803D")
            self.msg.setText(
                f"Conexão OK • Project Center {data.get('version','')}"
            )
        except Exception as exc:
            self.msg.setStyleSheet("color:#DC2626")
            self.msg.setText(
                "Não foi possível conectar ao servidor. "
                f"{exc}"
            )

    def server_config(self):
        url,ok=QInputDialog.getText(
            self,
            "Servidor",
            "URL HTTPS do Project Center",
            text=self.api.config["server_url"]
        )
        if ok and url:
            self.api.set_server(url.strip())
            self.update_server_info()
            self.test_server()

# QInputDialog missing import handled below
from PySide6.QtWidgets import QInputDialog

class MainWindow(QMainWindow):
    def __init__(self,api):
        super().__init__();self.api=api;self.setWindowTitle("Project Center");self.resize(1380,820);central=QWidget();self.setCentralWidget(central);h=QHBoxLayout(central);self.nav=QListWidget();self.nav.setFixedWidth(220);self.nav.setStyleSheet(f"QListWidget{{background:{BLUE};color:white;border:0;padding:8px}}QListWidget::item{{padding:12px;border-radius:7px}}QListWidget::item:selected{{background:#ffffff22}}")
        self.views=["Dashboard","Projetos","Notificações","Materiais"]+(["Administração"] if _is_admin_role(api.user["role"]) else [])
        self.nav.addItems(self.views);self.stack=QStackedWidget();h.addWidget(self.nav);h.addWidget(self.stack,1);self.pages={};
        for name in self.views:self.pages[name]=QWidget();self.stack.addWidget(self.pages[name])
        self.nav.currentRowChanged.connect(self.change_view);self.nav.setCurrentRow(0);self.tray=QSystemTrayIcon(self.style().standardIcon(QStyle.SP_ComputerIcon),self);self.tray.setToolTip('Project Center');self.tray.show();self.ws=WsThread(api);self.ws.event.connect(self.on_event);self.ws.start();self.timer=QTimer(self);self.timer.timeout.connect(self.ping);self.timer.start(30000)
    def closeEvent(self,e):self.ws.stop();super().closeEvent(e)
    def ping(self):
        try:self.api.post('/sessions/ping')
        except:pass
    def on_event(self,d):
        if d.get('type') in ('project_update','catalog_update','project_deleted') and self.nav.currentItem():self.change_view(self.nav.currentRow())
        if d.get('type')=='notification':
            n=d['notification'];self.statusBar().showMessage(n['title'],8000);self.tray.showMessage(n['title'],n['message'],QSystemTrayIcon.Information,8000)
            if n.get('kind')=='RESPONSIBILITY_TRANSFER':
                QMessageBox.information(self,'Transferência de responsabilidade',f"{n['title']}\n\n{n['message']}\n\nAbra Notificações para aceitar ou recusar.")
    def clear(self,w):
        lay=w.layout();
        if lay:
            while lay.count():
                i=lay.takeAt(0);x=i.widget();
                if x:x.deleteLater()
        else:w.setLayout(QVBoxLayout())
    def change_view(self,row):
        if row<0:return
        name=self.views[row];w=self.pages[name];self.clear(w)
        if name=='Dashboard':self.dashboard(w)
        elif name=='Projetos':self.projects(w)
        elif name=='Notificações':self.notifications(w)
        elif name=='Materiais':self.materials(w)
        elif name=='Administração':self.admin(w)
    def dashboard(self,w):
        v=w.layout();title=QLabel(f"Olá, {self.api.user['full_name']}");title.setStyleSheet("font-size:24px;font-weight:700");v.addWidget(title);d=self.api.get('/projects?page_size=100');cards=QHBoxLayout();
        for label,value in [('Projetos ativos',d['total']),('Meus projetos',sum(1 for p in d['items'] if p['current_responsible']['id']==self.api.user['id'])),('Com container',sum(1 for p in d['items'] if p['container_status']!='PROJETO SEM CONTAINER')),('Enviados',sum(1 for p in d['items'] if p['transport_stage']=='EQUIPAMENTOS ENVIADOS'))]:
            box=QLabel(f"<small>{label}</small><br><span style='font-size:28px;color:{BLUE2};font-weight:800'>{value}</span>");box.setStyleSheet("background:white;border:1px solid #E2E8F0;border-radius:10px;padding:18px");cards.addWidget(box)
        v.addLayout(cards);v.addWidget(QLabel("Projetos recentes"));table=self.project_table(d['items'][:15]);v.addWidget(table)
    def project_table(self,items):
        t=QTableWidget(len(items),6);t.setHorizontalHeaderLabels(['OS','Projeto','Cliente','Iniciado por','Responsável atual','Status']);t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);t.setSelectionBehavior(QAbstractItemView.SelectRows);t.setEditTriggers(QAbstractItemView.NoEditTriggers)
        for r,p in enumerate(items):
            vals=[p['os'],p['title'],p['client'],p['initiated_by']['full_name'],p['current_responsible']['full_name'],p['status']]
            for c,x in enumerate(vals):t.setItem(r,c,QTableWidgetItem(str(x)))
            t.item(r,0).setData(Qt.UserRole,p['id'])
        t.cellDoubleClicked.connect(lambda r,c:self.open_project(t.item(r,0).data(Qt.UserRole)));return t
    def projects(self,w):
        v=w.layout();bar=QHBoxLayout();q=QLineEdit();q.setPlaceholderText('Buscar OS, cliente ou projeto');b=QPushButton('Buscar');new=QPushButton('Novo projeto do Outlook');bar.addWidget(q);bar.addWidget(b);bar.addWidget(new);v.addLayout(bar);container=QVBoxLayout();v.addLayout(container)
        def load():
            while container.count():
                it=container.takeAt(0);x=it.widget();
                if x:x.deleteLater()
            d=self.api.get('/projects?page_size=100&q='+q.text());container.addWidget(self.project_table(d['items']))
        b.clicked.connect(load);new.clicked.connect(self.new_from_outlook);load()
    def new_from_outlook(self):
        try:
            d=selected_email_word();files={'file':(d['filename'],open(d['path'],'rb'),'application/vnd.openxmlformats-officedocument.wordprocessingml.document')};data={'os_value':d['os'],'client':d['client'],'title':d['title']};r=self.api._request('POST','/projects/from-word',data=data,files=files);QMessageBox.information(self,'Projeto','Projeto criado a partir do e-mail selecionado.');self.change_view(self.nav.currentRow())
        except Exception as e:QMessageBox.critical(self,'Novo projeto',str(e))
    def open_project(self,id):dlg=ProjectDialog(self.api,id,self);dlg.exec();self.change_view(self.nav.currentRow())
    def notifications(self,w):
        v=w.layout();inbox=self.api.get('/responsibility-transfers/inbox');v.addWidget(QLabel('Transferências aguardando sua decisão'))
        for x in inbox:
            row=QHBoxLayout();row.addWidget(QLabel(f"OS {x['os']} — {x['title']}\n{x['from_user']}: {x['reason']}"),1);a=QPushButton('Aceitar');r=QPushButton('Recusar');a.clicked.connect(lambda _,i=x['id']:self.decide(i,True));r.clicked.connect(lambda _,i=x['id']:self.decide(i,False));row.addWidget(a);row.addWidget(r);v.addLayout(row)
        v.addWidget(QLabel('Notificações'));n=self.api.get('/notifications');t=QTableWidget(len(n),3);t.setHorizontalHeaderLabels(['Data','Título','Mensagem']);t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for rr,x in enumerate(n):
            for c,val in enumerate([x['created_at'],x['title'],x['message']]):t.setItem(rr,c,QTableWidgetItem(str(val)))
        v.addWidget(t)
    def decide(self,id,accept):
        try:self.api.post(f'/responsibility-transfers/{id}/decision',json={'accept':accept});self.change_view(self.nav.currentRow())
        except Exception as e:QMessageBox.critical(self,'Transferência',str(e))
    def materials(self,w):
        v=w.layout();bar=QHBoxLayout();q=QLineEdit();q.setPlaceholderText('Buscar material');b=QPushButton('Buscar');bar.addWidget(q);bar.addWidget(b)
        if _is_admin_role(self.api.user['role']):
            imp=QPushButton('Importar Excel');imp.clicked.connect(self.import_materials);bar.addWidget(imp)
        v.addLayout(bar);holder=QVBoxLayout();v.addLayout(holder)
        def load():
            while holder.count():
                i=holder.takeAt(0);x=i.widget();
                if x:x.deleteLater()
            d=self.api.get('/materials?page_size=100&q='+q.text());t=QTableWidget(len(d['items']),6);t.setHorizontalHeaderLabels(['Código','Descrição','Centro','Depósito','UM','Ativo']);t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            for r,x in enumerate(d['items']):
                for c,val in enumerate([x['code'],x['description'],x['center'],x['deposit'],x['unit'],'SIM' if x['active'] else 'NÃO']):t.setItem(r,c,QTableWidgetItem(str(val)))
            holder.addWidget(t)
        b.clicked.connect(load);load()
    def import_materials(self):
        path,_=QFileDialog.getOpenFileName(self,'Catálogo','','Excel (*.xlsx *.xlsm)');
        if not path:return
        replace=QMessageBox.question(self,'Catálogo','Substituir catálogo atual?')==QMessageBox.Yes
        try:
            with open(path,'rb') as f:r=self.api._request('POST','/materials/import',data={'replace':'true' if replace else 'false'},files={'file':(os.path.basename(path),f,'application/vnd.ms-excel')}).json()
            QMessageBox.information(self,'Catálogo',f"{r['processed']} materiais processados.")
        except Exception as e:QMessageBox.critical(self,'Catálogo',str(e))
    def admin(self,w):
        v=w.layout();users=self.api.get('/admin/users');online=self.api.get('/admin/online-users');v.addWidget(QLabel(f"Usuários online agora: {len(online)}"));t=QTableWidget(len(users),6);t.setHorizontalHeaderLabels(['Nome','E-mail','Crachá','Perfil','Status','ID']);t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for r,x in enumerate(users):
            for c,val in enumerate([x['full_name'],x['email'],x['badge'],x['role'],x['status'],x['id']]):t.setItem(r,c,QTableWidgetItem(str(val)))
        v.addWidget(t);approve=QPushButton('Aprovar usuário selecionado');approve.clicked.connect(lambda:self.approve_selected(t));v.addWidget(approve)
    def approve_selected(self,t):
        r=t.currentRow();
        if r<0:return
        uid=int(t.item(r,5).text());roles=['OPERATOR','CONSULTA']+(['ADMIN'] if self.api.user['role']=='MASTER_ADMIN' else []);role,ok=QInputDialog.getItem(self,'Perfil','Perfil',roles,0,False)
        if ok:self.api.post(f'/admin/users/{uid}/approve',json={'role':role});self.change_view(self.nav.currentRow())

class ProjectDialog(QDialog):
    def __init__(self,api,id,parent=None):
        super().__init__(parent);self.api=api;self.id=id;self.resize(1050,760);self.setWindowTitle('Projeto');self.v=QVBoxLayout(self);self.load()
    def load(self):
        while self.v.count():
            i=self.v.takeAt(0);x=i.widget();
            if x:x.deleteLater()
        p=self.api.get(f'/projects/{self.id}');self.p=p;title=QLabel(f"OS {p['os']} — {p['title']}");title.setStyleSheet('font-size:22px;font-weight:700');self.v.addWidget(title);self.v.addWidget(QLabel(f"Iniciado por: {p['initiated_by']['full_name']}    |    Continuado por: {p['current_responsible']['full_name']}"));tabs=QTabWidget();self.v.addWidget(tabs,1);tabs.addTab(self.transfer_tab(p),'Consumíveis / Transferência');tabs.addTab(self.flow_tab(p),'Logística');tabs.addTab(self.timeline_tab(p),'Datas / histórico');tabs.addTab(self.responsibility_tab(p),'Responsabilidade');tabs.addTab(self.romaneio_tab(p),'Romaneio');tabs.addTab(self.docs_tab(p),'Documentos')
    def transfer_tab(self,p):
        w=QWidget()
        v=QVBoxLayout(w)

        try:
            status=self.api.get(
                f'/projects/{self.id}/transfer/status'
            )
            items=self.api.get(
                f'/projects/{self.id}/items'
            )
        except Exception as exc:
            v.addWidget(
                QLabel(
                    f'Erro ao carregar transferência: {exc}'
                )
            )
            return w

        status_label=QLabel(
            f"Status: {status['status']}   |   "
            f"Transferíveis: {status['transferable']}   |   "
            f"Revisão/não incluídos: {status['review']}"
        )
        status_label.setStyleSheet(
            'font-size:14px;font-weight:700;color:#003B7A'
        )
        v.addWidget(status_label)

        if status.get('sent_at'):
            v.addWidget(
                QLabel(
                    f"Enviada em: {status['sent_at']}"
                )
            )
        elif status.get('generated_at'):
            v.addWidget(
                QLabel(
                    f"Última planilha gerada em: "
                    f"{status['generated_at']}"
                )
            )

        t=QTableWidget(
            len(items),
            6
        )
        t.setHorizontalHeaderLabels(
            [
                'Código SAP',
                'Material',
                'Qtd',
                'UM',
                'Situação',
                'Transferir',
            ]
        )
        t.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        t.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        for r,x in enumerate(items):
            values=[
                x.get('material_code') or '-',
                x.get('matched_description')
                    or x.get('description')
                    or '-',
                x.get('quantity'),
                x.get('unit'),
                x.get('state'),
                'SIM' if x.get('transfer_eligible') else 'NÃO',
            ]
            for c,val in enumerate(values):
                t.setItem(
                    r,
                    c,
                    QTableWidgetItem(
                        str(val)
                    )
                )

        v.addWidget(
            t
        )

        info=QLabel(
            "Ao gerar, o Project Center baixa a planilha neste PC, "
            "abre o Outlook com os destinatários e o corpo prontos, "
            "mantém a assinatura padrão e anexa o XLSX. "
            "O e-mail NÃO é enviado automaticamente."
        )
        info.setWordWrap(
            True
        )
        v.addWidget(
            info
        )

        if p['can_edit']:
            bar=QHBoxLayout()

            prepare=QPushButton(
                'GERAR E ABRIR NO OUTLOOK'
            )
            prepare.clicked.connect(
                self.prepare_transfer_outlook
            )
            bar.addWidget(
                prepare
            )

            if (
                status.get('latest_document')
                and not status.get('sent')
            ):
                confirm=QPushButton(
                    'CONFIRMAR QUE ENVIEI'
                )
                confirm.clicked.connect(
                    self.confirm_transfer_sent
                )
                bar.addWidget(
                    confirm
                )

            v.addLayout(
                bar
            )

        return w

    def prepare_transfer_outlook(self):
        try:
            payload=self.api.post(
                f'/projects/{self.id}/transfer/prepare'
            )

            safe_name=payload['filename'].replace(
                '/',
                '_'
            )

            local_dir=Path(
                tempfile.gettempdir()
            )/'SYSTEM_PROJ_TRANSFERENCIAS'

            local_dir.mkdir(
                parents=True,
                exist_ok=True
            )

            local_path=(
                local_dir
                / safe_name
            )

            local_path.write_bytes(
                self.api.download(
                    f"/documents/"
                    f"{payload['document_id']}"
                    f"/download"
                )
            )

            open_transfer_draft(
                payload['recipients'],
                payload['subject'],
                payload['body_html'],
                local_path,
            )

            answer=QMessageBox.question(
                self,
                'Solicitação preparada',
                (
                    "O Outlook foi aberto com a planilha anexada.\n\n"
                    "Confira o e-mail e clique em ENVIAR no Outlook.\n\n"
                    "Depois de enviar, deseja confirmar agora no "
                    "Project Center que a solicitação foi enviada?"
                ),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if answer == QMessageBox.Yes:
                self.api.post(
                    f'/projects/{self.id}/transfer/confirm-sent'
                )

            self.load()

        except Exception as exc:
            QMessageBox.critical(
                self,
                'Solicitação de transferência',
                str(exc),
            )

    def confirm_transfer_sent(self):
        answer=QMessageBox.question(
            self,
            'Confirmar envio',
            (
                "Confirme somente se você realmente clicou em "
                "ENVIAR no Outlook.\n\n"
                "Marcar a solicitação como enviada?"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if answer != QMessageBox.Yes:
            return

        try:
            self.api.post(
                f'/projects/{self.id}/transfer/confirm-sent'
            )
            self.load()
        except Exception as exc:
            QMessageBox.critical(
                self,
                'Transferência',
                str(exc),
            )

    def flow_tab(self,p):
        w=QWidget()
        f=QFormLayout(w)
        self.forecast=QLineEdit(
            p['collection_forecast'] or ''
        )
        self.col=QCheckBox()
        self.col.setChecked(
            p['consumables_collected']
        )
        self.container=QComboBox()
        self.container.addItems(
            [
                'AGUARDANDO DEFINIÇÃO DO CONTAINER',
                'CONTAINER LOCADO',
                'CONTAINER SENDO CARREGADO',
                'CONTAINER ENVIADO',
                'PROJETO SEM CONTAINER',
            ]
        )
        self.container.setCurrentText(
            p['container_status']
        )
        self.transport=QComboBox()
        self.transport.addItems(
            [
                'AGUARDANDO PROGRAMAÇÃO DE TRANSPORTE',
                'PROGRAMAÇÃO DE TRANSPORTE ALINHADA',
                'CARREGANDO EQUIPAMENTOS NO CAMINHÃO',
                'EQUIPAMENTOS ENVIADOS',
            ]
        )
        self.transport.setCurrentText(
            p['transport_stage']
        )
        save=QPushButton(
            'Salvar logística'
        )
        save.clicked.connect(
            self.save_flow
        )
        f.addRow(
            'Previsão coleta',
            self.forecast
        )
        f.addRow(
            'Consumíveis coletados',
            self.col
        )
        f.addRow(
            'Situação do container',
            self.container
        )
        f.addRow(
            'Programação / transporte',
            self.transport
        )
        f.addRow(
            save
        )
        w.setEnabled(
            p['can_edit']
        )
        return w

    def save_flow(self):
        try:
            self.api.put(
                f'/projects/{self.id}/flow',
                json={
                    'version':self.p['version'],
                    'transfer_requested':None,
                    'collection_forecast':self.forecast.text(),
                    'consumables_collected':self.col.isChecked(),
                    'container_status':self.container.currentText(),
                    'transport_stage':self.transport.currentText(),
                }
            )
            self.load()
        except Exception as e:
            QMessageBox.critical(
                self,
                'Logística',
                str(e)
            )
            self.load()
    def timeline_tab(self,p):
        w=QWidget();v=QVBoxLayout(w);t=QTableWidget(len(p['stage_events']),3);t.setHorizontalHeaderLabels(['Data/hora','Área','Etapa']);t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for r,e in enumerate(p['stage_events']):
            for c,val in enumerate([e['occurred_at'],e['area'],e['stage']]):t.setItem(r,c,QTableWidgetItem(str(val)))
        v.addWidget(t);return w
    def responsibility_tab(self,p):
        w=QWidget();v=QVBoxLayout(w);t=QTableWidget(len(p['responsibility_history']),4);t.setHorizontalHeaderLabels(['Pessoa','Início','Fim','Motivo']);t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for r,h in enumerate(p['responsibility_history']):
            for c,val in enumerate([h['full_name'],h['started_at'],h['ended_at'] or 'Atual',h['reason'] or '']):t.setItem(r,c,QTableWidgetItem(str(val)))
        v.addWidget(t)
        if p['can_edit']:
            b=QPushButton('Solicitar transferência de responsabilidade');b.clicked.connect(self.request_transfer);v.addWidget(b)
        if _is_admin_role(self.api.user['role']):
            adm=QPushButton('Transferência administrativa (contingência)');adm.clicked.connect(self.admin_transfer);v.addWidget(adm)
        return w
    def request_transfer(self):
        users=self.api.get('/users/active');names=[x['full_name'] for x in users if x['id']!=self.p['current_responsible']['id']];lookup={x['full_name']:x['id'] for x in users};name,ok=QInputDialog.getItem(self,'Novo responsável','Pessoa',names,0,False)
        if not ok:return
        reason,ok=QInputDialog.getMultiLineText(self,'Motivo','Motivo da transferência (ex.: férias)')
        if ok and reason.strip():
            try:self.api.post(f'/projects/{self.id}/responsibility/request',json={'to_user_id':lookup[name],'reason':reason});QMessageBox.information(self,'Transferência','Solicitação enviada. A pessoa receberá um aviso no sistema.')
            except Exception as e:QMessageBox.critical(self,'Transferência',str(e))
    def admin_transfer(self):
        users=self.api.get('/users/active');names=[x['full_name'] for x in users if x['id']!=self.p['current_responsible']['id']];lookup={x['full_name']:x['id'] for x in users};name,ok=QInputDialog.getItem(self,'Transferência administrativa','Novo responsável',names,0,False)
        if not ok:return
        reason,ok=QInputDialog.getMultiLineText(self,'Motivo obrigatório','Informe o motivo da transferência administrativa')
        if ok and reason.strip():
            try:self.api.post(f'/projects/{self.id}/responsibility/admin-override',json={'to_user_id':lookup[name],'reason':reason});QMessageBox.information(self,'Transferência','Responsabilidade transferida e auditada.');self.load()
            except Exception as e:QMessageBox.critical(self,'Transferência',str(e))

    def romaneio_tab(self,p):
        w=QWidget();v=QVBoxLayout(w);items=self.api.get(f'/projects/{self.id}/romaneio');t=QTableWidget(len(items),5);t.setHorizontalHeaderLabels(['Categoria','Descrição','Qtd','UN','Origem']);t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for r,x in enumerate(items):
            for c,val in enumerate([x['category'],x['description'],x['quantity'],x['unit'],x['origin']]):t.setItem(r,c,QTableWidgetItem(str(val)))
        v.addWidget(t);bar=QHBoxLayout();add=QPushButton('+ Item');xlsx=QPushButton('Emitir XLSX');pdf=QPushButton('Emitir PDF');add.clicked.connect(self.add_romaneio);xlsx.clicked.connect(lambda:self.save_download('romaneio.xlsx'));pdf.clicked.connect(lambda:self.save_download('romaneio.pdf'));bar.addWidget(add);bar.addWidget(xlsx);bar.addWidget(pdf);v.addLayout(bar);return w
    def add_romaneio(self):
        cat,ok=QInputDialog.getItem(self,'Categoria','Categoria',['CONSUMÍVEIS','FERRAMENTAIS','INSTRUMENTOS','BANCADA','CONTAINER','EQUIPAMENTOS','LOCAÇÕES','OUTROS'],0,False)
        if not ok:return
        desc,ok=QInputDialog.getText(self,'Item','Descrição');
        if ok and desc:self.api.post(f'/projects/{self.id}/romaneio',json={'category':cat,'description':desc,'quantity':1,'unit':'UN'});self.load()
    def save_download(self,name):
        path,_=QFileDialog.getSaveFileName(self,'Salvar',name,'Todos (*.*)');
        if path:Path(path).write_bytes(self.api.download(f'/projects/{self.id}/{name}'));QMessageBox.information(self,'Arquivo','Arquivo gerado com sucesso.')
    def docs_tab(self,p):
        w=QWidget();v=QVBoxLayout(w);docs=self.api.get(f'/projects/{self.id}/documents');t=QTableWidget(len(docs),4);t.setHorizontalHeaderLabels(['Categoria','Arquivo','Versão','Data']);t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for r,x in enumerate(docs):
            for c,val in enumerate([x['category'],x['filename'],x['version'],x['created_at']]):t.setItem(r,c,QTableWidgetItem(str(val)))
        v.addWidget(t)
        if p['can_edit']:
            b=QPushButton('Incluir nova versão / documento');b.clicked.connect(self.upload_doc);v.addWidget(b)
        return w
    def upload_doc(self):
        path,_=QFileDialog.getOpenFileName(self,'Documento');
        if not path:return
        category,ok=QInputDialog.getItem(self,'Categoria','Categoria',['ROMANEIO','NOTA_FISCAL_SAIDA','NOTA_FISCAL_INSTRUMENTOS','NOTA_FISCAL_FERRAMENTAS','NOTA_FISCAL_LOCACAO','NOTA_FISCAL_COMPRAS','PEDIDO_COMPRA','CONTRATO_LOCACAO','COMPROVANTE','OUTROS'],0,False)
        if not ok:return
        with open(path,'rb') as f:self.api._request('POST',f'/projects/{self.id}/documents',data={'category':category,'logical_key':''},files={'file':(os.path.basename(path),f,'application/octet-stream')});self.load()

def run():
    app=QApplication(sys.argv);app.setStyleSheet(STYLE);api=ApiClient();login=LoginWindow(api);main_holder={}
    def open_main():
        login.hide();main=MainWindow(api);main_holder['main']=main;main.show()
    login.logged.connect(open_main);login.show();sys.exit(app.exec())
