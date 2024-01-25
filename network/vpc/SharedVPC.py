import pulumi_aws as aws

from pulumi import ComponentResource, ResourceOptions, export
from ipaddress import IPv4Network
from sortedcontainers import SortedList

from network.vpc.Subnet import Subnet, SubnetArgs, create_subnet
from network.vpc.NatGateway import NatGateway, NatGatewayArgs


PKG_REGISTRATION = "frgray:net:SharedVPC"


class SharedVPCArgs(object):
    def __init__(
        self,
        name: str,
        availability_zones: list,
        cidr_block: str = "10.10.0.0/16",
        dns_hostnames: bool = True,
        dns_support: bool = True,
    ) -> None:
        assert (
            len(availability_zones) == 3
        ), "You MUST provide 3 Availability Zone names"
        self.name = name
        self.availability_zones = availability_zones
        self.cidr_block = cidr_block
        self.dns_hostnames = dns_hostnames
        self.dns_support = dns_support


class SharedVPC(ComponentResource):
    def __init__(
        self, name: str, args: SharedVPCArgs, opts: ResourceOptions = None
    ) -> None:
        super().__init__(PKG_REGISTRATION, name, {}, opts)
        self.name = args.name
        self.availability_zones = SortedList(set(args.availability_zones))
        self.cidr_block = args.cidr_block
        self.dns_hostnames = args.dns_hostnames
        self.dns_support = args.dns_support
        self.ip_network = IPv4Network(args.cidr_block)

        self.create_vpc()
        self.create_igw()
        self.create_subnets()
        self.create_nat_gateways()
        self.create_route_tables()

    def create_vpc(self) -> None:
        self.vpc = aws.ec2.Vpc(
            self.name,
            cidr_block=self.cidr_block,
            enable_dns_hostnames=self.dns_hostnames,
            enable_dns_support=self.dns_support,
            tags={"Name": self.name},
            opts=ResourceOptions(parent=self),
        )

    def create_igw(self) -> None:
        self.internet_gateway = aws.ec2.InternetGateway(
            f"{self.name}-igw", vpc_id=self.vpc.id, tags={"Name": f"{self.name}-igw"}
        )

    def create_nat_gateways(self) -> None:
        self.nat_gateways = {}
        for index in self.subnets["public"]:
            subnet = self.subnets["public"][index]
            nat_gw = NatGateway(
                f"{self.name}-nat-{subnet.availability_zone}",
                args=NatGatewayArgs(
                    f"{self.name}-nat-{subnet.availability_zone}",
                    availability_zone=subnet.availability_zone,
                    subnet_id=subnet.id,
                ),
            )

            self.nat_gateways[subnet.availability_zone] = nat_gw

    def create_route_tables(self) -> {}:
        self.route_tables = {
            "public": aws.ec2.RouteTable(
                f"{self.name}-public",
                vpc_id=self.vpc.id,
                routes=[
                    aws.ec2.RouteTableRouteArgs(
                        cidr_block="0.0.0.0/0", gateway_id=self.internet_gateway.id
                    )
                ],
                tags={"Name": f'{self.name}-public'},
            ),
            "private": {},
        }

        for az in self.availability_zones:
            private = aws.ec2.RouteTable(
                f'{self.name}-private-{az}',
                vpc_id=self.vpc.id,
                routes=[
                    aws.ec2.RouteTableRouteArgs(
                        cidr_block="0.0.0.0/0", nat_gateway_id=self.nat_gateways[az].id
                    )
                ],
                tags={"Name": f'{self.name}-private-{az}'},
            )
            self.route_tables["private"][az] = private

    def create_subnets(self) -> None:
        self.subnets = {
            "private": self.create_private_subnets(),
            "public": self.create_public_subnets(),
        }

    def create_public_subnets(self) -> {}:
        subnets = {}
        for index in range(len(self.availability_zones)):
            networks = list(self.ip_network.subnets(prefixlen_diff=3))
            if index == 0:
                cidr_block = str(networks[-1])
            else:
                cidr_block = str(networks[-(index + 1)])
            print(f"Public CIDR block: {cidr_block}")
            subnets[self.availability_zones[index]] = create_subnet(
                name=f"{self.name}-public-{self.availability_zones[index]}",
                cidr_block=cidr_block,
                availability_zone=self.availability_zones[index],
                vpc_id=self.vpc.id,
                tags={"Name": f"{self.name}-public-{self.availability_zones[index]}"},
            )
        return subnets

    def create_private_subnets(self) -> None:
        subnets = {}
        for index in range(len(self.availability_zones)):
            networks = list(self.ip_network.subnets(prefixlen_diff=3))
            cidr_block = str(networks[index])
            print(f"Private CIDR block: {cidr_block}")
            subnets[self.availability_zones[index]] = create_subnet(
                name=f"{self.name}-private-{self.availability_zones[index]}",
                cidr_block=cidr_block,
                availability_zone=self.availability_zones[index],
                vpc_id=self.vpc.id,
                tags={"Name": f"{self.name}-private-{self.availability_zones[index]}"},
            )
        return subnets


export("SharedVPC", SharedVPC)
