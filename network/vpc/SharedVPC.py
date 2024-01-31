import pulumi_aws as aws

from pulumi import ComponentResource, ResourceOptions, export
from ipaddress import IPv4Network
from sortedcontainers import SortedList


PKG_REGISTRATION = "frgray:net:SharedVPC"


class SharedVPC(ComponentResource):
    def __init__(
        self,
        name: str,
        availability_zones: list,
        dns_hostnames: bool = True,
        dns_support: bool = True,
        cidr_block: str = "10.10.10.0/24",
        tags_all: dict = {},
        opts: ResourceOptions = None,
    ) -> None:
        super().__init__(PKG_REGISTRATION, name, {}, opts)
        self.name = name
        self.availability_zones = SortedList(set(availability_zones))
        self.cidr_block = cidr_block
        self.dns_hostnames = dns_hostnames
        self.dns_support = dns_support
        self.ip_network = IPv4Network(cidr_block)
        self.tags_all = tags_all

        self._create_vpc()
        self._create_igw()
        self._create_subnets()
        self._create_nat_gateways()
        self._create_route_tables()
        self._update_route_tables()

        self.register_outputs({})

    def _create_vpc(self) -> None:
        self.vpc = aws.ec2.Vpc(
            resource_name=self.name,
            cidr_block=self.cidr_block,
            enable_dns_hostnames=self.dns_hostnames,
            enable_dns_support=self.dns_support,
            tags={"Name": self.name},
            opts=ResourceOptions(parent=self),
        )

    def _create_igw(self) -> None:
        self.internet_gateway = aws.ec2.InternetGateway(
            f"{self.name}-igw", vpc_id=self.vpc.id, tags={"Name": f"{self.name}-igw"}
        )

    def _create_nat_gateways(self) -> None:
        self.nat_gateways = {}
        for az in self.subnets["private"]:
            subnet = self.subnets["private"][az]
            eip = aws.ec2.Eip(
                f"{self.name}-nat-{az}",
                domain="vpc",
                tags=self.tags_all,
                opts=ResourceOptions(parent=self, depends_on=[self.vpc, subnet]),
            )
            nat_gw = aws.ec2.NatGateway(
                f"{self.name}-nat-{az}",
                allocation_id=eip.allocation_id,
                subnet_id=subnet.id,
                tags=self.tags_all,
                opts=ResourceOptions(parent=self, depends_on=[self.vpc, subnet]),
            )
            self.nat_gateways[az] = nat_gw

    def _create_route_tables(self) -> None:
        self.route_tables = {
            "public": aws.ec2.RouteTable(
                f"{self.name}-public",
                vpc_id=self.vpc.id,
                routes=[
                    aws.ec2.RouteTableRouteArgs(
                        cidr_block="0.0.0.0/0",
                        gateway_id=self.internet_gateway.id.apply(lambda id: f"{id}"),
                    )
                ],
                tags={"Name": f"{self.name}-public"},
                opts=ResourceOptions(
                    parent=self, depends_on=[self.vpc, self.internet_gateway]
                ),
            ),
            "private": {},
        }

        for az in self.availability_zones:
            private = aws.ec2.RouteTable(
                f"{self.name}-private-{az}",
                vpc_id=self.vpc.id,
                routes=[
                    aws.ec2.RouteTableRouteArgs(
                        cidr_block="0.0.0.0/0",
                        nat_gateway_id=self.nat_gateways[az].id,
                    )
                ],
                tags={"Name": f"{self.name}-private-{az}"},
                opts=ResourceOptions(
                    parent=self, depends_on=[self.vpc, self.nat_gateways[az]]
                ),
            )
            self.route_tables["private"][az] = private

    def _create_subnets(self) -> None:
        self.subnets = {
            "private": self._create_private_subnets(),
            "public": self._create_public_subnets(),
        }

    def _create_public_subnets(self) -> dict:
        subnets = {}
        for index in range(len(self.availability_zones)):
            networks = list(self.ip_network.subnets(prefixlen_diff=3))
            if index == 0:
                cidr_block = str(networks[-1])
            else:
                cidr_block = str(networks[-(index + 1)])
            subnets[self.availability_zones[index]] = aws.ec2.Subnet(
                f"{self.name}-public-{self.availability_zones[index]}",
                vpc_id=self.vpc.id,
                cidr_block=cidr_block,
                availability_zone=self.availability_zones[index],
                tags={"Name": f"{self.name}-public-{self.availability_zones[index]}"},
                opts=ResourceOptions(parent=self, depends_on=self.vpc),
            )
        return subnets

    def _create_private_subnets(self) -> dict:
        subnets = {}
        for index in range(len(self.availability_zones)):
            networks = list(self.ip_network.subnets(prefixlen_diff=3))
            cidr_block = str(networks[index])
            subnets[self.availability_zones[index]] = aws.ec2.Subnet(
                f"{self.name}-private-{self.availability_zones[index]}",
                cidr_block=cidr_block,
                availability_zone=self.availability_zones[index],
                vpc_id=self.vpc.id,
                tags={"Name": f"{self.name}-private-{self.availability_zones[index]}"},
            )
        return subnets

    def _update_route_tables(self) -> None:
        for az in self.subnets["public"]:
            subnet = self.subnets["public"][az]
            route_table = self.route_tables["public"]
            aws.ec2.RouteTableAssociation(
                f"rtb-{az}-public",
                subnet_id=subnet.id,
                route_table_id=route_table.id,
                opts=ResourceOptions(parent=self, depends_on=[subnet, route_table]),
            )

        for az in self.subnets["private"]:
            print(f'AZ: {az}')
            subnet = self.subnets["private"][az]
            route_table = self.route_tables["private"][az]
            aws.ec2.RouteTableAssociation(
                f"rtb-{az}-private",
                subnet_id=subnet.id,
                route_table_id=route_table.id,
                opts=ResourceOptions(parent=self, depends_on=[subnet, route_table]),
            )


export("SharedVPC", SharedVPC)
