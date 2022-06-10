# Import credential and management objects.
from azure.identity import AzureCliCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
import os

print(f"Provisioning a virtual machine in Azure using Python.")

# Acquire credential object using CLI-based authentication.
credential = AzureCliCredential()

# Retrieve subscription ID from environment variable.
subscription_id = os.environ["AZURE_SUBSCRIPTION_ID"] = "a999ff42-7f72-4db3-ac67-7e123310fef6"


# 1 - create a resource group

# Get the management object for resources, this uses the credentials from the CLI login.
resource_client = ResourceManagementClient(credential, subscription_id)

# Set constants we need in multiple places.  You can change these values however you want.
RESOURCE_GROUP_NAME = "python-azure-vm-mytest-rg"
LOCATION = "eastus"

# create the resource group.
rg_result = resource_client.resource_groups.create_or_update(RESOURCE_GROUP_NAME,
    {
        "location": LOCATION
    }
)

print(f"Provisioned resource group {rg_result.name} in the {rg_result.location} region")

# 2 - provision the virtual network

# A virtual machine requires a network interface client (NIC). A NIC requires a virtual network (VNET) and subnet along with an IP address.  
# To support this requirement, we need to provision the VNET and Subnet first, then provision the NIC.

# Network and IP address names
VNET_NAME = "python-azure-vm-mytest-vnet"
SUBNET_NAME = "python-azure-vm-mytest-subnet"
IP_NAME = "python-azure-vm-mytest-ip"
IP_CONFIG_NAME = "python-azure-vm-mytest-ip-config"
NIC_NAME = "python-azure-vm-mytest-nic"

# Get the management object for the network
network_client = NetworkManagementClient(credential, subscription_id)

# Create the virtual network 
poller = network_client.virtual_networks.begin_create_or_update(RESOURCE_GROUP_NAME,
    VNET_NAME,
    {
        "location": LOCATION,
        "address_space": {
            "address_prefixes": ["10.0.0.0/16"]
        }
    }
)

vnet_result = poller.result()

print(f"Provisioned virtual network {vnet_result.name} with address prefixes {vnet_result.address_space.address_prefixes}")

# 3 - Create the subnet
poller = network_client.subnets.begin_create_or_update(RESOURCE_GROUP_NAME, 
    VNET_NAME, SUBNET_NAME,
    { "address_prefix": "10.0.0.0/24" }
)
subnet_result = poller.result()

print(f"Provisioned virtual subnet {subnet_result.name} with address prefix {subnet_result.address_prefix}")

# 4 - Create the IP address
poller = network_client.public_ip_addresses.begin_create_or_update(RESOURCE_GROUP_NAME,
    IP_NAME,
    {
        "location": LOCATION,
        "sku": { "name": "Standard" },
        "public_ip_allocation_method": "Static",
        "public_ip_address_version" : "IPV4"
    }
)

ip_address_result = poller.result()

print(f"Provisioned public IP address {ip_address_result.name} with address {ip_address_result.ip_address}")

# 5 - Create the network interface client
poller = network_client.network_interfaces.begin_create_or_update(RESOURCE_GROUP_NAME,
    NIC_NAME, 
    {
        "location": LOCATION,
        "ip_configurations": [ {
            "name": IP_CONFIG_NAME,
            "subnet": { "id": subnet_result.id },
            "public_ip_address": {"id": ip_address_result.id }
        }]
    }
)

nic_result = poller.result()

print(f"Provisioned network interface client {nic_result.name}")

# 6 - Create the virtual machine

# Get the management object for virtual machines
compute_client = ComputeManagementClient(credential, subscription_id)

VM_NAME = "PythonAzureVM"
USERNAME = "pythonazureuser"
PASSWORD = "Sreddy@1995"

print(f"Provisioning virtual machine {VM_NAME}; this operation might take a few minutes.")

# Create the VM (Ubuntu 18.04 VM)
# on a Standard DS1 v2 plan with a public IP address and a default virtual network/subnet.

poller = compute_client.virtual_machines.begin_create_or_update(RESOURCE_GROUP_NAME, VM_NAME,
    {
        "location": LOCATION,
        "storage_profile": {
            "image_reference": {
                "publisher": 'Canonical',
                "offer": "UbuntuServer",
                "sku": "16.04.0-LTS",
                "version": "latest"
            }
        },
        "hardware_profile": {
            "vm_size": "Standard_DS1_v2"
        },
        "os_profile": {
            "computer_name": VM_NAME,
            "admin_username": USERNAME,
            "admin_password": PASSWORD
        },
        "network_profile": {
            "network_interfaces": [{
                "id": nic_result.id,
            }]
        }
    }
)

vm_result = poller.result()

print(f"Provisioned virtual machine {vm_result.name}")