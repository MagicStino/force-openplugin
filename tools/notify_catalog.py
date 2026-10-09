"""Private SMTP notification for catalog proposals; recipient and credentials are secrets."""
import json, os, smtplib, ssl, sys
from email.message import EmailMessage

def send():
    names = ['CATALOG_NOTIFY_TO','CATALOG_SMTP_HOST','CATALOG_SMTP_PORT','CATALOG_SMTP_USER','CATALOG_SMTP_PASSWORD','CATALOG_SMTP_FROM']
    cfg = {k: os.environ.get(k, '') for k in names}
    if not all(cfg.values()):
        print('Email notifications are not configured; no message sent.')
        return
    event = json.loads(open(os.environ['GITHUB_EVENT_PATH']).read())
    issue = event.get('issue')
    if issue and not issue.get('title', '').startswith(('[Catalog]', '[Maintainer]')):
        print('Not a catalog proposal or maintainer application; no message sent.')
        return
    port = int(cfg['CATALOG_SMTP_PORT'])
    if port not in (465, 587):
        raise ValueError('SMTP port must be 465 or 587')
    msg = EmailMessage()
    msg['From'] = cfg['CATALOG_SMTP_FROM']; msg['To'] = cfg['CATALOG_NOTIFY_TO']
    msg['Subject'] = 'OpenPlugin community submission' if issue else 'OpenPlugin notification test'
    text = 'Private notification test: email delivery is configured.'
    if issue:
        text = f"{issue.get('title', '')[:200]}\nSubmitted by: {issue.get('user', {}).get('login', '')}\n{issue.get('html_url', '')}\n\n{(issue.get('body') or '')[:12000]}\n\nReview on GitHub. Use Actions > Accept catalog submission to prepare a catalog pull request."
    msg.set_content(text)
    context = ssl.create_default_context()
    client = smtplib.SMTP_SSL(cfg['CATALOG_SMTP_HOST'], port, timeout=30, context=context) if port == 465 else smtplib.SMTP(cfg['CATALOG_SMTP_HOST'], port, timeout=30)
    with client:
        if port == 587:
            client.ehlo(); client.starttls(context=context); client.ehlo()
        client.login(cfg['CATALOG_SMTP_USER'], cfg['CATALOG_SMTP_PASSWORD']); client.send_message(msg)
    print('Private notification sent.')

if __name__ == '__main__':
    try: send()
    except Exception: sys.exit('Email delivery failed. Check private SMTP settings; no credentials or recipient were logged.')
