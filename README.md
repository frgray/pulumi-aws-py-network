
# Pulumi Abstracted VPC Compontent Resource
Provides a custom Pulumi/Python ComponentResource (SharedVPC) object that creates a VPC with 3 public/private subnets in a /24 range along with 3 Nat Gateways, 3 private route tables, and 1 public route table.

## Resources Created
- VPC
- 1 Internet Gateway
- 3 Public Subnets
- 3 Private Subnets
- 3 ElasticIPs
- 3 NAT Gateways
- 3 AZ-specific private RouteTables
- 1 Public Route Table

## Example Usage
```python
import pulumi
import pulumi_aws as aws

from network.vpc import SharedVPC

config = pulumi.Config()
vpc_name = config.require('vpc_name')
cidr_block = config.require('cidr_block')

azs = aws.get_availability_zones(state="available")

created_vpc = SharedVPC(name=name,
                        availability_zones=azs.names[0:3],
                        cidr_block=cidr_block,
                        tags_all={"env": "dev"}
                        )

```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| name | The Name of the VPC | `str` | - |  yes | 
| cidr_block | The CIDR Block of the VPC | `str` | `10.10.10.0/24` |  no | 
| availability_zones | Availability Zone Names of the VPC | `list(str)` | - |  yes | 
| dns_hostnames | Enable DNS Hostname Support | `bool` | `True` |  no | 
| dns_support | Enable DNS Support | `bool` | `True` |  no | 
| tags_all | The tags to be attached to all resources | `dict` | `{}` |  no | 
