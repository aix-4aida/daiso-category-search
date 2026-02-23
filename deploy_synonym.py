"""Deploy synonym fix to Lightsail with correct API key."""
import json, subprocess, os
from dotenv import load_dotenv
load_dotenv(override=True)

new_key = os.getenv("GOOGLE_API_KEY")

# Get latest image tag
sub = subprocess.run(['aws', 'lightsail', 'get-container-images', '--service-name', 'daiso-search-service'], capture_output=True, text=True)
images = json.loads(sub.stdout)['containerImages']
back_img = next(img['image'] for img in images if 'backend-synonym-fix' in img['image'])
print(f"Image: {back_img}")

# Get current deployment
sub = subprocess.run(['aws', 'lightsail', 'get-container-services', '--service-name', 'daiso-search-service'], capture_output=True, text=True)
svc = json.loads(sub.stdout)['containerServices'][0]
deployment = svc['currentDeployment']
containers = deployment['containers']
containers['backend']['image'] = back_img
containers['backend']['environment']['GOOGLE_API_KEY'] = new_key

with open('deploy_payload_synonym.json', 'w') as f:
    json.dump({'containers': containers, 'publicEndpoint': deployment['publicEndpoint']}, f)

sub2 = subprocess.run(['aws', 'lightsail', 'create-container-service-deployment', '--service-name', 'daiso-search-service', '--cli-input-json', 'file://deploy_payload_synonym.json'], capture_output=True, text=True)
if sub2.returncode == 0:
    v = json.loads(sub2.stdout).get('containerService',{}).get('nextDeployment',{}).get('version','?')
    print(f"✅ Deployment v{v} triggered!")
else:
    print(f"❌ Failed: {sub2.stderr[:300]}")
