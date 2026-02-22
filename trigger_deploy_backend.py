import json, subprocess

with open('lightsail_services_latest.json') as f:
    data = json.load(f)

deployment = data['containerServices'][0]['currentDeployment']
if 'nextDeployment' in data['containerServices'][0]:
    deployment = data['containerServices'][0]['nextDeployment']

containers = deployment['containers']
# Update Backend Image
if 'backend' in containers:
    containers['backend']['image'] = ':daiso-search-service.backend-search-fixes.37'

endpoint = deployment['publicEndpoint']

with open('deploy_payload_backend.json', 'w') as f:
    json.dump({'containers': containers, 'publicEndpoint': endpoint}, f)

sub = subprocess.run([
    'aws', 'lightsail', 'create-container-service-deployment',
    '--service-name', 'daiso-search-service',
    '--cli-input-json', 'file://deploy_payload_backend.json'
], capture_output=True, text=True)
print(sub.stdout)
if sub.stderr: print('Error:', sub.stderr)

