from __future__ import annotations
import os, re, tempfile

def selected_email_word():
    try: import win32com.client as win32
    except Exception as e: raise RuntimeError("Outlook Desktop/pywin32 não disponível") from e
    outlook=win32.Dispatch("Outlook.Application"); explorer=outlook.ActiveExplorer()
    if not explorer or explorer.Selection.Count==0: raise RuntimeError("Selecione um e-mail no Outlook")
    email=explorer.Selection.Item(1); subject=str(email.Subject or ""); m=re.search(r"\bOS\s*[:\-]?\s*(\d+)",subject,re.I); os_value=m.group(1) if m else ""
    sem_os=re.sub(r"\s*[-|]\s*OS\s*[:\-]?\s*\d+.*$","",subject,flags=re.I).strip(); parts=[x.strip() for x in re.split(r"\s+-\s+",sem_os) if x.strip()]; client=parts[0] if parts else ""; title=" - ".join(parts[1:]) if len(parts)>1 else sem_os
    candidates=[]
    for a in email.Attachments:
        name=str(a.FileName)
        if name.lower().endswith(".docx"): candidates.append((0 if "CONSUM" in name.upper() else 1,name,a))
    if not candidates: raise RuntimeError("Nenhum DOCX encontrado no e-mail")
    _,name,a=sorted(candidates,key=lambda x:x[0])[0]; path=os.path.join(tempfile.gettempdir(),name);a.SaveAsFile(path);return {"os":os_value,"client":client,"title":title,"path":path,"filename":name}



def open_transfer_draft(
    recipients,
    subject,
    body_html,
    attachment_path,
):
    """
    Abre um rascunho no Outlook Desktop.

    IMPORTANTE:
    - NÃO envia a mensagem;
    - preserva a assinatura padrão carregada pelo Outlook;
    - adiciona o corpo da solicitação acima da assinatura;
    - anexa a planilha gerada pelo Project Center.

    Esta função precisa ser executada no PC do colaborador onde o
    Outlook Desktop está instalado. Um servidor remoto não consegue
    automatizar o Outlook do PC cliente diretamente.
    """
    try:
        import time
        import win32com.client as win32
    except Exception as exc:
        raise RuntimeError(
            "Outlook Desktop/pywin32 não disponível neste computador."
        ) from exc

    attachment_path = os.path.abspath(
        str(attachment_path)
    )

    if not os.path.isfile(
        attachment_path
    ):
        raise RuntimeError(
            f"Anexo não encontrado: {attachment_path}"
        )

    outlook_app = win32.Dispatch(
        "Outlook.Application"
    )

    mail = outlook_app.CreateItem(
        0
    )

    # O Outlook normalmente insere a assinatura padrão quando a
    # janela é exibida. Só depois capturamos o HTMLBody.
    mail.Display()

    # Pequena espera para o WordEditor/assinatura terminar de carregar.
    time.sleep(
        0.8
    )

    signature_html = (
        mail.HTMLBody
        or ""
    )

    mail.To = "; ".join(
        recipients
    )

    mail.Subject = (
        subject
    )

    separator = (
        "<br><br>"
        if signature_html
        else ""
    )

    mail.HTMLBody = (
        body_html
        + separator
        + signature_html
    )

    mail.Attachments.Add(
        attachment_path
    )

    mail.Display()

    return True
