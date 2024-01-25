import pulumi_aws as aws

from pulumi import ComponentResource, ResourceOptions, export


PKG_REGISTRATION = "frgray:net:NatGateway"


class NatGatewayArgs(object):
    def __init__(
        self, name: str, availability_zone: str, subnet_id: str, tags: dict = {}
    ) -> None:
        self.name = name
        self.availability_zone = availability_zone
        self.subnet_id = subnet_id
        self.tags = tags


class NatGateway(ComponentResource):
    def __init__(
        self, name: str, args: NatGatewayArgs, opts: ResourceOptions = None
    ) -> None:
        super().__init__(PKG_REGISTRATION, name, {}, opts)
        self.eip = aws.ec2.Eip(f"{name}-eip", vpc=True, tags=args.tags)
        self.nat_gateway = aws.ec2.NatGateway(
            name,
            allocation_id=self.eip.allocation_id,
            subnet_id=args.subnet_id,
            tags=args.tags,
        )


export("NatGateway", NatGateway)
