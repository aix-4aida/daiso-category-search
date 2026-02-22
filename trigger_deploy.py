import json, subprocess
with open('lightsail_services.json') as f:
    data = json.load(f)
deployment = data['containerServices'][0]['currentDeployment']
containers = deployment['containers']
containers['backend']['image'] = ':daiso-search-service.backend-latest.31'
containers['frontend']['image'] = ':daiso-search-service.frontend-latest.32'
endpoint = deployment['publicEndpoint']

with open('deploy_payload.json', 'w') as f:
    json.dump({'containers': containers, 'publicEndpoint': endpoint}, f)

sub = subprocess.run([
    'aws', 'lightsail', 'create-container-service-deployment',
    '--service-name', 'daiso-search-service',
    '--cli-input-json', 'file://deploy_payload.json'
], capture_output=True, text=True)
print(sub.stdout)
if sub.stderr: print('Error:', sub.stderr)

