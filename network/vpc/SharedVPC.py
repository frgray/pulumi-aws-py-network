import pulumi_aws as aws

from pulumi import ComponentResource, ResourceOptions, export
from ipaddress import IPv4Network
from sortedcontainers import SortedList

from Subnet import Subnet, SubnetArgs, create_subnet
from NatGateway import NatGateway, NatGatewayArgs



PKG_REGISTRATION='frgray:net:SharedVPC'

class SharedVPCArgs(object):
    def __init__(self,
                 name: str,
                 availability_zones: list,
                 cidr_block: str = "10.10.0.0/16",
                 dns_hostnames: bool = True,
                 dns_support: bool = True) -> None:
        assert len(availability_zones) == 3, "You MUST provide 3 Availability Zone names"
        self.name = name
        self.availability_zones = availability_zones
        self.cidr_block = cidr_block
        self.dns_hostnames = dns_hostnames
        self.dns_support = dns_support


class SharedVPC(ComponentResource):
    def __init__(self,
                 name: str,
                 args: SharedVPCArgs,
                 opts: ResourceOptions = None) -> None:
        
        super().__init__(PKG_REGISTRATION, name, {}, opts)
        self.name = args.vpc_name
        self.cidr_block = args.cidr_block
        self.dns_hostnames = args.dns_hostnames
        self.dns_support = args.dns_support
        self.availability_zones = SortedList(set(args.availability_zones))

        # self.region = aws.get_region()
        self.create_vpc()
        self.create_igw()
        self.subnets = self.create_subnets()
        self.ip_network = IPv4Network(args.cidr_block)
        self.route_tables = self.create_route_tables()

    def create_vpc(self) -> None:
        self.vpc = aws.ec2.Vpc(
            self.vpc_name,
            cidr_block=self.cidr_block,
            enable_dns_hostnames=self.dns_hostnames,
            enable_dns_support=self.dns_support,
            tags={
                'Name': self.vpc_name
            },
            opts=ResourceOptions(parent=self)
        )

    def create_igw(self) -> None:
        self.internet_gateway = {
            "default": aws.ec2.InternetGateway(vpc_id = self.vpc.id, 
                                               tags={"Name": f'{self.vpc_name}-igw'}
                                               )
        }
        
    def create_nat_gateways(self) -> None:
        self.nat_gateways = {
            self.availability_zones[0]: create_subnet(name=f'{self.name}-nat-{self.availability_zones[0]}', 
                                                       cidr_block=self.ip_network[0],
                                                       availability_zone=self.availability_zones[0]),

            self.availability_zones[1]: create_subnet(name=f'{self.name}-nat-{self.availability_zones[1]}', 
                                                       cidr_block=self.ip_network[1],
                                                       availability_zone=self.availability_zones[1]),
                                                       
            self.availability_zones[2]: create_subnet(name=f'{self.name}-nat-{self.availability_zones[2]}', 
                                                       cidr_block=self.ip_network[2],
                                                       availability_zone=self.availability_zones[2])
        }

    def create_nat_gateways(self) -> None:
        pass

    def create_route_tables(self) -> {}:
        public = aws.ec2.route_table(vpc_id = self.vpc.id,
                                     routes=[
                                         aws.ec2.RouteTableRouteArgs(
                                             cidr_block="0.0.0.0/0",
                                             gateway_id=self.internet_gateway.id
                                         )
                                     ],
                                     tags={"Name": f'{self.vpc_name}-public'})
        nat_az_a = aws.ec2.route_table(vpc_id = self.vpc.id,
                                        routes=[
                                            aws.ec2.RouteTableRouteArgs(
                                                cidr_block="0.0.0.0/0",
                                                nat_gateway_id=self.nat_gateways
                                            )
                                        ],
                                        tags={"Name": f'{self.vpc_name}-public'})
        nat_az_b = ""
        nat_az_c = ""

    def create_subnets(self) -> {}:
        self.subnets = {
            "private": self.create_private_subnets(),
            "public": self.create_public_subnets()
        }
        
    def create_public_subnets(self) -> {}:
        aws.ec2.Subnet("foo", 
                       vpc_id=self.vpc.id,
                       cidr_block="",
                       availability_zone=azs[0]
                       tags={}
                       )
        pass



    def create_private_subnets(self) -> None:
        aws.ec2.Subnet(args.name,
                       vpc_id=args.vpc_id,
                       cidr_block=args.cidr_block,
                       customer_owned_ipv4_pool=False,
                       ipv6_native=False,
                       enable_dns64=False,
                       assign_ipv6_address_on_creation=False,
                       tags=args.tags
                       )    
    

    def create_route_tables(self) -> {}:
        pass

export('SharedVPC', SharedVPC)