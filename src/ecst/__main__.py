import argparse
import boto3
import json
import subprocess

parser = argparse.ArgumentParser(
                    prog='ecs-tunnel',
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
  print('services_response')
  print(services_response)

service_arn = [k for k in services_response['serviceArns'] if args.service in k][0]

if args.verbose:
  print('service_arn')
  print(service_arn)

list_tasks_response = ecsClient.list_tasks(
  cluster=args.cluster,
  serviceName=service_arn
)

if args.verbose:
  print('list_tasks_response')
  print(list_tasks_response)

task_arn = list_tasks_response['taskArns'][0]
task_id = task_arn.split('/')[-1]

tasks_response = ecsClient.describe_tasks(
  cluster=args.cluster,
  tasks=[task_arn]
)

if args.verbose:
  print('tasks_response')
  print(tasks_response)

container_id = tasks_response['tasks'][0]['containers'][0]['runtimeId']

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
