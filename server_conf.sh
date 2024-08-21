# Instalacion y configuracion del servidor kubernetes en Debian 12
# Entornos de desarrollo
apt install sudo git curl jq -y
curl -fsSL https://deb.nodesource.com/setup_22.x -o nodesource_setup.sh
bash nodesource_setup.sh
apt-get install -y nodejs
apt install python3-pip python3-venv -y 
sudo apt install -y pkg-config 
sudo apt install -y default-libmysqlclient-dev
node -v

# Configurar red 
# Guia: https://reintech.io/blog/configuring-network-interfaces-debian-12

# Sudo
# Guia: https://itslinuxguide.com/add-users-sudoers-file-debian/

# Configuracion de Kubernetes
# Guia: https://www.bentasker.co.uk/posts/documentation/linux/building-a-k8s-cluster-on-debian-12-1-bookworm.html 
# Puertos: TCP/6443: The port used by the Kubernetes API server
# TCP/2379-2380: Used by the etcd API
# TCP/10250: The Kubelet API
# TCP/10257: Kube Controller Manager (see note below)
# TCP/10259: Kube scheduler (see note below)
# TCP/30000-32767: Nodeport services


#cat <<EOF | tee /etc/modules-load.d/containerd.conf
#overlay
#br_netfilter
#EOF

#modprobe overlay
#modprobe br_netfilter

#cat <<EOF | tee /etc/sysctl.d/99-kubernetes-k8s.conf
#net.bridge.bridge-nf-call-iptables = 1
#net.ipv4.ip_forward = 1
#net.bridge.bridge-nf-call-ip6tables = 1
#EOF

#sysctl --system


#apt update
#apt install -y containerd


#containerd config default > /etc/containerd/config.toml


#nano /etc/containerd/config.toml

#And look for the section [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options], under which there should be an attribute called SystemdCgroup: change this to true so that SystemD cgroups are used:

#[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
#   SystemdCgroup = true
#

#systemctl enable containerd
#systemctl restart containerd

swapoff -a
nano /etc/fstab # comment out the swap line

cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.ipv4.ip_forward = 1
EOF



# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y

sudo apt-get install -y containerd
sudo systemctl restart containerd

#Modificar /etc/containerd/config.toml

version = 2

[plugins]
  [plugins."io.containerd.grpc.v1.cri"]
    sandbox_image = "registry.k8s.io/pause:3.10"
    
    [plugins."io.containerd.grpc.v1.cri".cni]
      bin_dir = "/usr/lib/cni"
      conf_dir = "/etc/cni/net.d"
    
    [plugins."io.containerd.grpc.v1.cri".containerd]
      disable_snapshot_annotations = true
      
      [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
        runtime_type = "io.containerd.runc.v2"

  [plugins."io.containerd.internal.v1.opt"]
    path = "/var/lib/containerd/opt"


# Instalacion de herramientas Kubernetes
# Guia: https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/
sudo apt-get update
# apt-transport-https may be a dummy package; if so, you can skip that package
sudo apt-get install -y apt-transport-https ca-certificates curl gpg
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.31/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
sudo systemctl enable --now kubelet

#kubeadm init --control-plane-endpoint=$HOSTNAME
sudo kubeadm init --pod-network-cidr=192.168.0.0/16

# Configuracion de calico
# https://docs.tigera.io/calico/latest/getting-started/kubernetes/quickstart

kubectl taint nodes --all node-role.kubernetes.io/control-plane-
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml

# MySQL
# Ultima version repo mysql
# https://dev.mysql.com/downloads/repo/apt/
wget https://dev.mysql.com/get/mysql-apt-config_0.8.32-1_all.deb
export PATH=$PATH:/usr/local/sbin:/usr/sbin:/sbin
dpkg -i mysql-apt-config_0.8.32-1_all.deb
apt update
apt install mysql-server -y
systemctl enable mysql
systemctl start mysql
mysql_secure_installation
# Configurar base de datos y permisos
# CREATE DATABASE k8s_management;


# Configuracion de proyecto (Pruebas)

git clone https://github.com/valdiviesod/kubepy -b dev





