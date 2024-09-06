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

if (args.verbose):
  print('---')
  print('args:', args)
  print('---')

session = boto3.Session(profile_name=args.aws_profile, region_name=args.region)
ecsClient = session.client('ecs')
ssmClient = session.client('ssm')

services_response = ecsClient.list_services(
  cluster=args.cluster
)

if args.verbose:
  print('services:', services_response)

service_arn = [k for k in services_response['serviceArns'] if args.service in k][0]

if args.verbose:
  print('service_arn:', service_arn)

list_tasks_response = ecsClient.list_tasks(
  cluster=args.cluster,
  serviceName=service_arn
)

if args.verbose:
  print('tasks:', list_tasks_response)

task_arn = list_tasks_response['taskArns'][0]
task_id = task_arn.split('/')[-1]

if args.verbose:
  print('task_arn:', task_arn)

tasks_response = ecsClient.describe_tasks(
  cluster=args.cluster,
  tasks=[task_arn]
)

if args.verbose:
  print('---')
  print('tasks:', tasks_response)
  print('---')

containers = tasks_response['tasks'][0]['containers']

if args.verbose:
  print('---')
  print('containers:', containers)
  print('---')

container_id = None
# Loop through containers to find one with the same name as the service
# (There is sometimes a `ecs-service-connect` container so cannot rely on there being 1 container, or 1st container)
for container in containers:
  if container['name'] == args.service:
    container_id = container['runtimeId']
container_id = containers[0]['runtimeId']

if container_id is None:
  raise Exception(f"Cannot find a container runtimeId for %s" % args.service)

if args.verbose:
  print('---')
  print('container_id:', container_id)
  print('---')

target=f"ecs:%s_%s_%s" % (args.cluster, task_id, container_id)

if args.verbose:
  print('---')
  print('target:', target)
  print('---')

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

if args.verbose:
  print('ssm_response:', ssm_response)

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
