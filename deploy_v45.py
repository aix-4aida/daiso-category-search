"""Deploy v45 with cache-busted frontend."""
import json, subprocess, os
from dotenv import load_dotenv
load_dotenv(override=True)
new_key = os.getenv("GOOGLE_API_KEY")

sub = subprocess.run(['aws', 'lightsail', 'get-container-images', '--service-name', 'daiso-search-service'], capture_output=True, text=True)
images = json.loads(sub.stdout)['containerImages']
back_img = next(img['image'] for img in images if 'backend-score-fix' in img['image'])
front_img = next(img['image'] for img in images if 'frontend-v44-cache' in img['image'])
print(f"Backend: {back_img}\nFrontend: {front_img}")

sub = subprocess.run(['aws', 'lightsail', 'get-container-services', '--service-name', 'daiso-search-service'], capture_output=True, text=True)
svc = json.loads(sub.stdout)['containerServices'][0]
deployment = svc['currentDeployment']
containers = deployment['containers']
containers['backend']['image'] = back_img
containers['backend']['environment']['GOOGLE_API_KEY'] = new_key
containers['frontend']['image'] = front_img

with open('deploy_payload_v45.json', 'w') as f:
    json.dump({'containers': containers, 'publicEndpoint': deployment['publicEndpoint']}, f)

sub2 = subprocess.run(['aws', 'lightsail', 'create-container-service-deployment', '--service-name', 'daiso-search-service', '--cli-input-json', 'file://deploy_payload_v45.json'], capture_output=True, text=True)
if sub2.returncode == 0:
    v = json.loads(sub2.stdout).get('containerService',{}).get('nextDeployment',{}).get('version','?')
    print(f"✅ Deployment v{v} triggered!")
else:
    print(f"❌ Failed: {sub2.stderr[:300]}")
