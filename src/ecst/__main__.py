import argparse
import boto3
import json
import subprocess
import signal

def handler(signum, frame):
    print('\nExiting...')
    exit (0)

signal.signal(signal.SIGINT, handler)

parser = argparse.ArgumentParser(
                    prog='ecst',
                    description='Create local tunnels and sessions to AWS ECS services running in a VPC',)
parser.add_argument('cluster',
                    help='The name of the ECS cluster')
parser.add_argument('service',
                    help='The name of the ECS service')
parser.add_argument('--local-port', default=3001)
parser.add_argument('--remote-port', default=3000)
parser.add_argument('--region', default="eu-west-2")
parser.add_argument('--aws-profile', default="default")
parser.add_argument('--verbose', action='store_true')

args = parser.parse_args()

ecsClient = boto3.client('ecs')
ssmClient = boto3.client('ssm')

services_response = ecsClient.list_services(
  cluster=args.cluster
)

if args.verbose:
  print('---services_response---')
  print(services_response)

service_arn = [k for k in services_response['serviceArns'] if args.service in k][0]

if args.verbose:
  print('---service_arn---')
  print(service_arn)

list_tasks_response = ecsClient.list_tasks(
  cluster=args.cluster,
  serviceName=service_arn
)

if args.verbose:
  print('---list_tasks_response---')
  print(list_tasks_response)

task_arn = list_tasks_response['taskArns'][0]
task_id = task_arn.split('/')[-1]

if args.verbose:
  print('---task_arn---')
  print(task_arn)
  print('---task_id---')
  print(task_id)

tasks_response = ecsClient.describe_tasks(
  cluster=args.cluster,
  tasks=[task_arn]
)

if args.verbose:
  print('---tasks_response---')
  print(tasks_response)

container_id = None
containers = tasks_response['tasks'][0]['containers']

# Loop through containers to find one with the same name as the service
# (There is sometimes a `ecs-service-connect` container so cannot rely on there being 1 container, or 1st container)
for container in containers:
  if container['name'] == args.service:
    container_id = container['runtimeId']

if container_id is None:
  raise Exception(f"Cannot find a container runtimeId for %s" % args.service)

target=f"ecs:%s_%s_%s" % (args.cluster, task_id, container_id)

ssm_response = ssmClient.start_session(
  Target=target,
  DocumentName="AWS-StartPortForwardingSession",
  Parameters={
    "portNumber": [
      str(args.remote_port),
    ],
    "localPortNumber": [
      str(args.local_port),
    ],
  }
)

cmd = [
    '/usr/local/sessionmanagerplugin/bin/session-manager-plugin',
    json.dumps(ssm_response),
    args.region,
    'StartSession',
    args.aws_profile,
    json.dumps(dict(Target=target)),
    f'https://ssm.%s.amazonaws.com' % (args.region)
]

subprocess.run(cmd)
