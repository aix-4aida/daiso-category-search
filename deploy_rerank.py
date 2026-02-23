"""Deploy reranker fix to Lightsail with correct API key."""
import json
import subprocess
import os
from dotenv import load_dotenv
load_dotenv(override=True)

new_key = os.getenv("GOOGLE_API_KEY")

# Get latest backend image tag
sub = subprocess.run(
    ['aws', 'lightsail', 'get-container-images', '--service-name', 'daiso-search-service'],
    capture_output=True, text=True
)
images = json.loads(sub.stdout)['containerImages']
back_img = None
for img in images:
    if 'backend-rerank-fix' in img['image']:
        back_img = img['image']
        break
print(f"Backend image: {back_img}")

# Get current deployment
sub = subprocess.run(
    ['aws', 'lightsail', 'get-container-services', '--service-name', 'daiso-search-service'],
    capture_output=True, text=True
)
svc = json.loads(sub.stdout)['containerServices'][0]
deployment = svc['currentDeployment']
containers = deployment['containers']

# Update backend image AND API key
containers['backend']['image'] = back_img
containers['backend']['environment']['GOOGLE_API_KEY'] = new_key
endpoint = deployment['publicEndpoint']

with open('deploy_payload_rerank.json', 'w') as f:
    json.dump({'containers': containers, 'publicEndpoint': endpoint}, f)

sub2 = subprocess.run(
    ['aws', 'lightsail', 'create-container-service-deployment',
     '--service-name', 'daiso-search-service',
     '--cli-input-json', 'file://deploy_payload_rerank.json'],
    capture_output=True, text=True
)
if sub2.returncode == 0:
    v = json.loads(sub2.stdout).get('containerService',{}).get('nextDeployment',{}).get('version','?')
    print(f"✅ Deployment v{v} triggered!")
else:
    print(f"❌ Failed: {sub2.stderr[:300]}")
