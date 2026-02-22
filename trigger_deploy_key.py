import json, subprocess, os
from dotenv import load_dotenv

load_dotenv()
new_key = os.environ.get('GOOGLE_API_KEY')

with open('lightsail_services_key.json') as f:
    data = json.load(f)

deployment = data['containerServices'][0]['currentDeployment']
if 'nextDeployment' in data['containerServices'][0]:
    deployment = data['containerServices'][0]['nextDeployment']

containers = deployment['containers']
# Update Google API Key
if 'backend' in containers and 'environment' in containers['backend']:
    containers['backend']['environment']['GOOGLE_API_KEY'] = new_key

endpoint = deployment['publicEndpoint']

with open('deploy_payload_key.json', 'w') as f:
    json.dump({'containers': containers, 'publicEndpoint': endpoint}, f)

sub = subprocess.run([
    'aws', 'lightsail', 'create-container-service-deployment',
    '--service-name', 'daiso-search-service',
    '--cli-input-json', 'file://deploy_payload_key.json'
], capture_output=True, text=True)
print(sub.stdout)
if sub.stderr: print('Error:', sub.stderr)

