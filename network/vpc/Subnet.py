import pulumi_aws as aws

from pulumi import ComponentResource, ResourceOptions, export

# from ipaddress import IP

PKG_REGISTRATION = "frgray:net:Subnet"


class SubnetArgs(object):
    def __init__(
        self,
        cidr_block: str,
        vpc_id: str,
        availability_zone: str,
        tags: dict,
    ) -> None:
        self.cidr_block = cidr_block
        self.vpc_id = vpc_id
        self.availability_zone = availability_zone
        self.tags = tags


class Subnet(ComponentResource):
    def __init__(
        self, name: str, args: SubnetArgs, opts: ResourceOptions = None
    ) -> None:
        super().__init__(PKG_REGISTRATION, name, {}, opts)
        self.availability_zone = args.availability_zone
        self.cidr_block = args.cidr_block
        self.vpc_id = args.vpc_id
        self.availability_zone = args.availability_zone
        self.tags = args.tags
        self.name = name
        self._subnet = aws.ec2.Subnet(
            self.name,
            vpc_id=args.vpc_id,
            cidr_block=args.cidr_block,
            ipv6_native=False,
            enable_dns64=False,
            assign_ipv6_address_on_creation=False,
            tags=args.tags,
        )
        self.id = self._subnet.id


def create_subnet(
    name: str, cidr_block: str, availability_zone: str, vpc_id: str, tags: dict = {}
) -> Subnet:
    return Subnet(
        name=name,
        args=SubnetArgs(
            cidr_block=cidr_block,
            availability_zone=availability_zone,
            vpc_id=vpc_id,
            tags=tags,
        ),
    )


export("Subnet", Subnet)
