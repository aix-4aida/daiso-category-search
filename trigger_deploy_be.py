import json, subprocess
with open('lightsail_services.json') as f:
    data = json.load(f)
deployment = data['containerServices'][0]['currentDeployment']
if 'nextDeployment' in data['containerServices'][0]:
    deployment = data['containerServices'][0]['nextDeployment']

containers = deployment['containers']
containers['backend']['image'] = ':daiso-search-service.backend-nlu-fix.35'
endpoint = deployment['publicEndpoint']

with open('deploy_payload_be.json', 'w') as f:
    json.dump({'containers': containers, 'publicEndpoint': endpoint}, f)

sub = subprocess.run([
    'aws', 'lightsail', 'create-container-service-deployment',
    '--service-name', 'daiso-search-service',
    '--cli-input-json', 'file://deploy_payload_be.json'
], capture_output=True, text=True)
print(sub.stdout)
if sub.stderr: print('Error:', sub.stderr)

