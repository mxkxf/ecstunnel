# ecst

Create local tunnels and sessions to AWS ECS services running in a VPC.

## Prerequesites

- Python 3
- [AWS CLI Session Manager plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)

## Installation

Install from [PyPI](https://pypi.org/project/ecst):

```bash
pip install ecst
```

## Usage

```bash
usage: python -m ecst [-h] [--local-port LOCAL_PORT] [--remote-port REMOTE_PORT]
            [--region REGION] [--aws-profile AWS_PROFILE] [--verbose]
            cluster service
```
