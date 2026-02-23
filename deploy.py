import json, subprocess

# Get latest images
sub = subprocess.run(['aws', 'lightsail', 'get-container-images', '--service-name', 'daiso-search-service'], capture_output=True, text=True)
images_data = json.loads(sub.stdout)

front_img = None
back_img = None

for img in images_data['containerImages']:
    if 'frontend-ui-fixes-3' in img['image']:
        front_img = img['image']
    if 'backend-search-fixes-3' in img['image']:
        back_img = img['image']
        
    if front_img and back_img:
        break

print(f'Frontend: {front_img}')
print(f'Backend: {back_img}')

if not front_img or not back_img:
    print('Error finding images.')
    exit(1)

# Get current deployment info
sub = subprocess.run(['aws', 'lightsail', 'get-container-services', '--service-name', 'daiso-search-service'], capture_output=True, text=True)
svcs = json.loads(sub.stdout)
deployment = svcs['containerServices'][0]['currentDeployment']
if 'nextDeployment' in svcs['containerServices'][0]:
    deployment = svcs['containerServices'][0]['nextDeployment']

containers = deployment['containers']
containers['frontend']['image'] = front_img
containers['backend']['image'] = back_img
endpoint = deployment['publicEndpoint']

with open('deploy_payload_v33.json', 'w') as f:
    json.dump({'containers': containers, 'publicEndpoint': endpoint}, f)

sub2 = subprocess.run([
    'aws', 'lightsail', 'create-container-service-deployment',
    '--service-name', 'daiso-search-service',
    '--cli-input-json', 'file://deploy_payload_v33.json'
], capture_output=True, text=True)

print('Deploy Output:', sub2.stdout)
if sub2.stderr:
    print('Deploy Error:', sub2.stderr)
