import subprocess,json,os,pathlib
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import AuthorizedSession
from colab_cli.client import Client,Prod
os.environ['COLAB_CLI_REQUEST_TIMEOUT']='25'
root=pathlib.Path(__file__).resolve().parent
r=subprocess.run([r'<YOUR_GCLOUD_SDK_BIN>\gcloud.cmd','auth','print-access-token'],capture_output=True,text=True,timeout=30,check=True)
sess=AuthorizedSession(Credentials(token=r.stdout.strip()))
client=Client(Prod(),sess)
result={}
try:
 resp=sess.get('https://www.googleapis.com/oauth2/v2/userinfo',timeout=20)
 result['identity_http_status']=resp.status_code
 if resp.ok: result['email']=resp.json().get('email')
except Exception as e: result['identity_error_type']=type(e).__name__
try:
 result['consumption']=client.get_consumption_user_info().model_dump(mode='json')
except Exception as e:
 result['consumption_error_type']=type(e).__name__
 result['consumption_http_status']=getattr(getattr(e,'response',None),'status_code',None)
try:
 resp=sess.get('https://www.googleapis.com/drive/v3/files/18c1OsVpp31rx8Kv1XtERjb9CkY2BwaMx',params={'fields':'id,name,owners(emailAddress,displayName)'},timeout=20)
 result['notebook_http_status']=resp.status_code
 if resp.ok: result['notebook']=resp.json()
except Exception as e: result['notebook_error_type']=type(e).__name__
(root/'colab_account_probe.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))