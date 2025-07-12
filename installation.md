# Installation Guide

## Create first VM (master)
This will be a template VM which has all the necessary software installed and configured, it will later be cloned to create the other VMs. This one will later become the master.

- Create a VM and name it `master` with the following specifications:
    - CPU: 2 cores
    - RAM: 2GB
    - Disk Size: 25GB
- Create a Nat-Network on 10.0.2.0/24
- Configure the NAT-Network to forward ports 30080 and 30081 to the VM with IP address `10.0.2.11`
- Set the VMs network adapter to the NAT-Network

### Setup OS
- Install Ubuntu Server 24.04 LTS on the VM
- Update the system with `sudo apt update && sudo apt upgrade -y`
- Disable automatic network configuration by creating `/etc/cloud/cloud.cfg.d/99-disable-network-config.cfg` and setting it to `{config: disabled}`
- Set a static IP address for the VM in `/etc/netplan/01-static-ip.yaml` with this configuration:
    ```bash
    network:
        version: 2
        renderer: networkd
        ethernets:
        enp0s3:
            addresses:
            - 10.0.2.10/24
            routes:
            - to:   0.0.0.0/0
                via: 10.0.2.1
            nameservers:
            addresses:
                - 1.1.1.1
                - 8.8.8.8
        enp0s8:
            dhcp4: no
            addresses:
            - 192.168.56.200/24
    ```
    - Apply the configuration with `sudo netplan apply`
- Edit `/etc/hostname` to set the hostname to `master`
- Allow Ports 30080 and 30081 through the firewall with `sudo ufw allow 30080/tcp` and `sudo ufw allow 30081/tcp`
- Install the nfs-client package with `sudo apt-get install nfs-common`
- Mount the NFS folder by adding this line to `/etc/fstab`:
    ```bash
    10.0.2.10:/srv/nfs/shared   /mnt   nfs   defaults,_netdev   0   0
    ```
### Install Docker
- Install Docker by running:
    ```bash
    # Add Dockers official GPG key:
    sudo apt-get update
    sudo apt-get install ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc

    # Add the repository to Apt sources:
    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    sudo usermod -aG docker $USER
    ```
- Allow docker to the local insecure registry by adding the following line to `/etc/docker/daemon.json`
    ```json
    {
    "insecure-registries": ["10.0.2.10:5000"]
    }
    ```
- Restart Docker service with `sudo systemctl restart docker`
### Install Kubernetes
- Disable Swap by editing the `/etc/fstab` file and commenting out or removing the line that mounts swap space.
- Install Kubernetes by running these commands:
    ```bash
    sudo apt-get update
    sudo apt-get install -y apt-transport-https ca-certificates curl gpg
    sudo mkdir -p -m 755 /etc/apt/keyrings
    curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.33/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

    echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.33/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
    sudo apt-get update
    sudo apt-get install -y kubelet kubeadm kubectl
    sudo apt-mark hold kubelet kubeadm kubectl
    sudo systemctl enable --now kubelet
    ```

## Create the other VMs
Now we use the template to create two more VMs by cloning them through VirtualBox's Clone feature. We'll name these `worker1` and `worker2`. 

- Edit the `/etc/netplan/01-netcfg.yaml` file on each worker node to configure static IP addresses for the network interfaces. The addresses should be `10.0.2.11` on `worker1` and `10.0.2.12` on `worker2`.
- Apply the changes by running `sudo netplan apply` on each worker node.
- Set the hostname of each worker node to `worker1` or `worker2` respectively by editing the `/etc/hostname` file and then restarting the system with `sudo reboot`.

## Setting up the master node
### Setup the NFS Server
- Install the NFS server by running these commands on the master node:

    ```bash
    sudo apt install nfs-kernel-server
    sudo mkdir -p /srv/nfs/shared/mariadb/
    sudo chown -R dnsmasq:systemd-journal /srv/nfs/shared/mariadb/
    sudo chmod -R 755 /srv/nfs/shared
    ```
- Export the NFS share using the following line in `/etc/exports` file:
    ```bash
    /srv/nfs/shared 10.0.2.10/16(rw,sync,no_subtree_check,no_root_squash)
    ```
- Apply the export using:
    ```bash
    sudo exportfs -a
    sudo systemctl restart nfs-kernel-server
    sudo systemctl enable nfs-kernel-server
    ```
### Setup the Docker Image Registry
- Download and start the docker registry container by running the following command:
    ```bash
    docker run -d -p 5000:5000 --restart=always --name registry registry:2
    ```
- Transfer the images to master:
    - Build them on your local machine using `docker-compose up --build`
    - Save them as tar files using: 
        ```bash
        docker image save virtualisierungimageprocessing-frontend -o frontend.tar
        docker image save virtualisierungimageprocessing-backend -o backend.tar
        docker image save virtualisierungimageprocessing-image-editor-bw -o image-editor-bw.tar
        docker image save virtualisierungimageprocessing-image-editor-rembg -o image-editor-rembg.tar
        ```
    - Tranfer them by mounting a Virtual Box Shared Folder on the master node and copying the tar files to it.
    - On the master load them using:
        ```bash
        docker image load -i frontend.tar
        docker image load -i backend.tar
        docker image load -i image-editor-bw.tar
        docker image load -i image-editor-rembg.tar
        ```
- Add the images to the Docker registry on master by tagging them with the registry address and pushing them:
    ```bash
    docker tag virtualisierungimageprocessing-frontend:latest 10.0.2.10:5000/imageprocessing-frontend:vdm6
    docker tag virtualisierungimageprocessing-backend:latest 10.0.2.10:5000/imageprocessing-backend:vdm5
    docker tag virtualisierungimageprocessing-image-editor-bw:latest 10.0.2.10:5000/imageprocessing-image-editor-bw:vdm3
    docker tag virtualisierungimageprocessing-image-editor-bw:latest 10.0.2.10:5000/imageprocessing-image-editor-rembg:vdm4

    docker push 10.0.2.10:5000/imageprocessing-frontend:vdm6
    docker push 10.0.2.10:5000/imageprocessing-backend:vdm5
    docker push 10.0.2.10:5000/imageprocessing-image-editor-bw:vdm3
    docker push 10.0.2.10:5000/imageprocessing-image-editor-rembg:vdm4
    ```

### Setup the Kubernetes Cluster
- Create the Cluster using kubeadm with Calico as the network plugin
    ```bash
    sudo kubeadm init --pod-network-cidr=192.168.0.0/16 --cri-socket /run/cri-dockerd.sock
    ```
    - Note down the join command from the output of the above command
- Create the kubeconfig 
    ```bash
    mkdir -p $HOME/.kube
    sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
    sudo chown $(id -u):$(id -g) $HOME/.kube/config
    ```
- Apply the Calico network plugin to the cluster
    ```bash
    kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.2/manifests/calico.yaml
    ```
    - This takes about a minute, you can check when its done by running `kubectl get nodes` and waiting until the master is ready.

- Install Kubernetes Metrics API for the Horizontal Pod Autoscaler to work properly:
    ```bash
    kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
    ```

- Configure RBAC for the application roles and permissions:
    ```bash
    # Generate private keys
    openssl genrsa -out tim.key 2048
    openssl genrsa -out max.key 2048

    # Generate a certificate signing request
    openssl req -new -key tim.key -out tim.csr -subj "/CN=tim/O=developer"
    openssl req -new -key max.key -out max.csr -subj "/CN=max/O=viewer"

    # Sign the certificate 
    sudo openssl x509 -req -in tim.csr -CA /etc/kubernetes/pki/ca.crt -CAkey /etc/kubernetes/pki/ca.key -CAcreateserial -out tim.crt -days 365
    sudo openssl x509 -req -in max.csr -CA /etc/kubernetes/pki/ca.crt -CAkey /etc/kubernetes/pki/ca.key -CAcreateserial -out max.crt -days 365

    # Use kubeconfig to automatically use the signed certificate and key when talking to the cluster
    kubectl config set-credentials tim --client-certificate=/home/tim/tim.crt --client-key=/home/tim/tim.key
    kubectl config set-context developer-context --cluster=kubernetes --namespace=stateless --user=tim

    kubectl config set-credentials max --client-certificate=/home/tim/max.crt --client-key=/home/tim/max.key
    kubectl config set-context viewer-context --cluster=kubernetes --namespace=stateless --user=max
    ```
    - You can now switch between contexts using one of these:
        ```bash
        kubectl config use-context developer-context
        kubectl config use-context viewer-context
        kubectl config use-context kubernetes-admin@kubernetes
        ```

- Create namespaces using:
    ```bash
    kubectl create namespace stateless
    kubectl create namespace stateful
    ```

## Join the Cluster on the Worker Nodes
- Run the join command you received when creating the cluster on each worker node to add them to the cluster.
    - This should look something like this:
        ```bash
        kubeadm join 10.0.2.10:6443 --token <token> \
            --discovery-token-ca-cert-hash <sha256:xxx> --cri-socket unix:///var/run/cri-dockerd.sock
        ```
- Make sure its working using:
    ```bash
    kubectl get nodes
    ```
    - This should show all three nodes in the cluster and, after about a minute, they should be marked as ready.

## Deploy the Applications from the Master Node 
- Move the manifests to the master node either by reusing the Shared Folder or just by cloning the repository.
- Apply the manifests to deploy the stateless application using:
    ```bash
    kubectl apply -f frontend.yaml -f backend.yaml -f image-editor-bw.yaml -f image-editor-bg.yaml role-developer.yaml role-viewer.yaml roleBinding-developer.yaml roleBinding-viewer.yaml
    ```
- Apply the manifests to deploy the stateful application using:
    ```bash
    kubectl apply -f pv.yaml -f secrets.yaml -f ghost-deployment.yaml -f mariadb-statefulset.yaml -f nginx-deployment.yaml pv.yaml
    ```


