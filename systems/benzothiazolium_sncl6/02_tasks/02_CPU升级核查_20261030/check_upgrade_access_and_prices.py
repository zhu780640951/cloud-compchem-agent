import subprocess,requests,json,pathlib,concurrent.futures
from html.parser import HTMLParser
root=pathlib.Path(__file__).resolve().parent
r=subprocess.run([r'<YOUR_GCLOUD_SDK_BIN>\gcloud.cmd','auth','print-access-token'],capture_output=True,text=True,check=True,timeout=30)
headers={'Authorization':'Bearer '+r.stdout.strip()}
base='https://compute.googleapis.com/compute/v1/projects/<YOUR_GCP_PROJECT_ID>'
permissions=['compute.instances.get','compute.instances.setMachineType','compute.instances.start','compute.instances.stop']
resp=requests.post(base+'/zones/us-central1-a/instances/orca-cpu-16/testIamPermissions',headers=headers,json={'permissions':permissions},timeout=25)
report={'iam_http_status':resp.status_code,'iam':resp.json()}
(root/'iam_upgrade_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
class VisibleText(HTMLParser):
 def __init__(self): super().__init__();self.skip=0;self.parts=[]
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style'): self.skip+=1
 def handle_endtag(self,tag):
  if tag in ('script','style'): self.skip=max(0,self.skip-1)
 def handle_data(self,data):
  if not self.skip and data.strip(): self.parts.append(data.strip())
try:
 response=requests.get('https://cloud.google.com/products/compute/pricing/general-purpose?hl=en',timeout=35)
 parser=VisibleText();parser.feed(response.text);text='\n'.join(parser.parts)
 (root/'official_pricing_visible_text.txt').write_text(text,encoding='utf-8')
 for heading in ['N2 custom vCPUs and memory','N2 extended custom memory']:
  start=text.find(heading)
  print('PRICE_SECTION',heading,'position',start)
  if start>=0: print(text[start:start+5500])
except Exception as error: print('PRICING_FETCH_ERROR',type(error).__name__)