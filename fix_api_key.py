"""Update Lightsail deployment with the NEW Google API key from .env"""
import json
import subprocess
import os
from dotenv import load_dotenv

# Load the NEW key from .env
load_dotenv(override=True)
new_key = os.getenv("GOOGLE_API_KEY")
print(f"New GOOGLE_API_KEY from .env: {new_key[:10]}...{new_key[-4:]}")

# Get current deployment
sub = subprocess.run(
    ['aws', 'lightsail', 'get-container-services', '--service-name', 'daiso-search-service'],
    capture_output=True, text=True
)
data = json.loads(sub.stdout)
svc = data['containerServices'][0]
deployment = svc['currentDeployment']

containers = deployment['containers']

# Update the environment variable for backend container
if 'backend' in containers:
    if 'environment' not in containers['backend']:
        containers['backend']['environment'] = {}
    old_key = containers['backend']['environment'].get('GOOGLE_API_KEY', 'NOT SET')
    print(f"Old GOOGLE_API_KEY in Lightsail: {old_key[:10]}...{old_key[-4:]}")
    containers['backend']['environment']['GOOGLE_API_KEY'] = new_key
    print(f"Updated to: {new_key[:10]}...{new_key[-4:]}")

endpoint = deployment['publicEndpoint']

payload = {'containers': containers, 'publicEndpoint': endpoint}
with open('deploy_payload_key_fix.json', 'w') as f:
    json.dump(payload, f)

# Deploy
sub2 = subprocess.run(
    ['aws', 'lightsail', 'create-container-service-deployment',
     '--service-name', 'daiso-search-service',
     '--cli-input-json', 'file://deploy_payload_key_fix.json'],
    capture_output=True, text=True
)

if sub2.returncode == 0:
    result = json.loads(sub2.stdout)
    version = result.get('containerService', {}).get('nextDeployment', {}).get('version', '?')
    print(f"\n✅ Deployment v{version} triggered successfully with new API key!")
else:
    print(f"\n❌ Deployment failed!")
    print(sub2.stderr[:500])
