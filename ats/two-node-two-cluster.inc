# This is a boilerplate script rather than an actual test..

litp create -p /software/profiles/rhel_6_4 -t os-profile -o name='sample-profile' path='/profiles/node-iso/'

litp create -p /infrastructure/systems/system1 -t system -o system_name='MN1VM'
litp create -p /infrastructure/systems/system2 -t system -o system_name='MN2VM'

litp create -p /infrastructure/networking/networks/nodes -t network -o subnet='10.4.23.0/24' litp_management=true name=nodes 

litp create -p /infrastructure/storage/storage_profiles/profile_1 -t storage-profile-base

litp create -p /deployments/site1 -t deployment
litp create -p /deployments/site1/clusters/cluster1 -t cluster
litp create -p /deployments/site1/clusters/cluster2 -t cluster

litp create -p /deployments/site1/clusters/cluster1/nodes/node1 -t node -o hostname='node1'
litp inherit -p /deployments/site1/clusters/cluster1/nodes/node1/system -s /infrastructure/systems/system1
litp inherit -p /deployments/site1/clusters/cluster1/nodes/node1/os -s /software/profiles/rhel_6_4
litp inherit -p /deployments/site1/clusters/cluster1/nodes/node1/storage_profile -s /infrastructure/storage/storage_profiles/profile_1

litp create -p /deployments/site1/clusters/cluster2/nodes/node2 -t node -o hostname='node2'
litp inherit -p /deployments/site1/clusters/cluster2/nodes/node2/system -s /infrastructure/systems/system2
litp inherit -p /deployments/site1/clusters/cluster2/nodes/node2/os -s /software/profiles/rhel_6_4
litp inherit -p /deployments/site1/clusters/cluster2/nodes/node2/storage_profile -s /infrastructure/storage/storage_profiles/profile_1


litp create -p /ms/network_interfaces/if0 -t network-interface -o network_name=nodes ipaddress=10.4.23.50
litp create -p /deployments/site1/clusters/cluster1/nodes/node1/network_interfaces/if0 -t network-interface -o network_name=nodes ipaddress=10.4.23.51 
litp create -p /deployments/site1/clusters/cluster2/nodes/node2/network_interfaces/if0 -t network-interface -o network_name=nodes ipaddress=10.4.23.52
