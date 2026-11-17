import os,sys,pathlib,json,webbrowser
from urllib.parse import urlparse
root=pathlib.Path(__file__).resolve().parent
project=root.parent.parent
tool=project/'连接配置'/'colab-cli'
os.environ['CLOUDSDK_CONFIG']=str(tool/'gcloud-auth')
os.environ['GOOGLE_APPLICATION_CREDENTIALS']=str(tool/'gcloud-auth'/'application_default_credentials.json')
os.environ['COLAB_CLI_REQUEST_TIMEOUT']='45'
from colab_cli.common import state
from colab_cli.history import HistoryLogger

def open_drive_authorization(uri, directory=root, opener=webbrowser.open):
    parsed=urlparse(uri)
    if parsed.scheme!='https' or parsed.hostname!='accounts.google.com':
        raise ValueError('Expected the official Google account authorization URL')
    directory=pathlib.Path(directory)
    (directory/'本次Drive授权链接.txt').write_text(uri,encoding='utf-8')
    try:
        requested=bool(opener(uri,new=2,autoraise=True))
        error_type=None
    except Exception as error:
        requested=False
        error_type=type(error).__name__
    status={'browser_open_requested':requested,'error_type':error_type,'user_authorization_confirmed':False}
    (directory/'browser_open_status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')
    print('[project] Browser open requested. Complete Google authorization in the browser.' if requested else '[project] Could not open browser automatically; use 本次Drive授权链接.txt.',flush=True)
    return status

def main():
    history=HistoryLogger(str(root/'cli_history'))
    original_log_event=history.log_event
    def log_event(name,event_type,data):
        original_log_event(name,event_type,data)
        if event_type=='drive_auth_needed':
            open_drive_authorization(data['uri'])
    history.log_event=log_event
    state._history=history
    from colab_cli.commands import automation
    original_run_automation=automation.run_automation
    def run_automation(name,op,code,allow_stdin=False,path=None,timeout=None):
        if op=='drivemount':
            code=f'from google.colab import drive\ndrive.mount({path!r}, timeout_ms=600000)'
            timeout=900
        return original_run_automation(name,op,code,allow_stdin=allow_stdin,path=path,timeout=timeout)
    automation.run_automation=run_automation
    from colab_cli.cli import app
    app(args=['--auth','adc','--config',str(tool/'sessions.json')]+sys.argv[1:])

if __name__=='__main__':
    main()