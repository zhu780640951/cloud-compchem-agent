import subprocess,json,os,pathlib,datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import AuthorizedSession
from colab_cli.client import Client,Prod
os.environ['COLAB_CLI_REQUEST_TIMEOUT']='25'
root=pathlib.Path(__file__).resolve().parent
r=subprocess.run([r'<YOUR_GCLOUD_SDK_BIN>\gcloud.cmd','auth','print-access-token'],capture_output=True,text=True,timeout=30)
result={'method':'existing gcloud short-lived access token, in memory only','runtime_created':False}
if r.returncode:
 result.update(ok=False,stage='gcloud_token',reason='existing login token unavailable')
else:
 sess=AuthorizedSession(Credentials(token=r.stdout.strip()))
 client=Client(Prod(),sess)
 try:
  assignments=client.list_assignments()
  result.update(ok=True,stage='list_assignments',count=len(assignments),sessions=[{'endpoint':a.endpoint,'accelerator':a.accelerator.value,'machine_shape':a.machine_shape.name} for a in assignments])
 except Exception as e:
  response=getattr(e,'response',None)
  result.update(ok=False,stage='list_assignments',error_type=type(e).__name__,http_status=getattr(response,'status_code',None))
  if response is not None:
   try:
    data=response.json()
    err=data.get('error',{}) if isinstance(data,dict) else {}
    if isinstance(err,dict): result['server_reason']=err.get('message')
   except Exception: pass
(root/'colab_existing_login_probe.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))