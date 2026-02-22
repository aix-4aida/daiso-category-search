import json, subprocess
with open('lightsail_services.json') as f:
    data = json.load(f)
deployment = data['containerServices'][0]['currentDeployment']
containers = deployment['containers']
containers['frontend']['image'] = ':daiso-search-service.frontend-ui-polish.33'
endpoint = deployment['publicEndpoint']

with open('deploy_payload_ui.json', 'w') as f:
    json.dump({'containers': containers, 'publicEndpoint': endpoint}, f)

sub = subprocess.run([
    'aws', 'lightsail', 'create-container-service-deployment',
    '--service-name', 'daiso-search-service',
    '--cli-input-json', 'file://deploy_payload_ui.json'
], capture_output=True, text=True)
print(sub.stdout)
if sub.stderr: print('Error:', sub.stderr)

