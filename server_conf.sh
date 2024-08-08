# Instalacion y configuracion del servidor kubernetes en Debian 12
#https://www.marioverhaeg.nl/2024/06/18/install-a-clean-kubernetes-cluster-on-debian-12look-for-the-section-plugins-io-containerd-grpc-v1-cri-containerd-runtimes-runc-options-and-change-systemd/
apt install sudo git curl -y
curl -fsSL https://deb.nodesource.com/setup_22.x -o nodesource_setup.sh
bash nodesource_setup.sh
apt-get install -y nodejs
node -v

# Configurar red primero
# Guia: https://reintech.io/blog/configuring-network-interfaces-debian-12

# Sudo
# Guia: https://itslinuxguide.com/add-users-sudoers-file-debian/
# Ejecutar comandos como root

# Configuracion de Kubernetes
# Guia: https://www.bentasker.co.uk/posts/documentation/linux/building-a-k8s-cluster-on-debian-12-1-bookworm.html 
# Puertos: TCP/6443: The port used by the Kubernetes API server
# TCP/2379-2380: Used by the etcd API
# TCP/10250: The Kubelet API
# TCP/10257: Kube Controller Manager (see note below)
# TCP/10259: Kube scheduler (see note below)
# TCP/30000-32767: Nodeport services

systemctl mask dev-sda3.swap
sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab
reboot

sudo swapoff -a
nano /etc/fstab # comment out the swap line

cat <<EOF | tee /etc/modules-load.d/containerd.conf 
overlay 
br_netfilter
EOF

sudo modprobe overlay && sudo modprobe br_netfilter

cat <<EOF | tee /etc/sysctl.d/99-kubernetes-k8s.conf
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1 
net.bridge.bridge-nf-call-ip6tables = 1 
EOF

apt-get update && apt-get install containerd -y

containerd config default | tee /etc/containerd/config.toml >/dev/null 2>&1

nano /etc/containerd/config.toml


# Instalacion de herramientas Kubernetes
# Guia: https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/
apt install gnupg gnupg2 curl software-properties-common -y
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmour -o /etc/apt/trusted.gpg.d/cgoogle.gpg
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list

apt-get update && apt-get install kubelet kubeadm kubectl -y && apt-mark hold kubelet kubeadm kubectl
sudo sysctl -w net.ipv4.ip_forward=1


ln -s /sbin/ebtables /usr/bin/ebtables
ln -s /sbin/ethtool /usr/bin/ethtool
ln -s /sbin/tc /usr/bin/tc
ln -s /sbin/conntrack /usr/bin/conntrack
ln -s /sbin/iptables /usr/bin/iptables

sudo sysctl -w net.ipv4.ip_forward=1

# Ignorar errores de preflight por paquetes que ya existen
kubeadm init --pod-network-cidr=192.168.0.0/16
#sudo kubeadm init --pod-network-cidr=192.168.0.0/16 --ignore-preflight-errors=all --kubelet-extra-args="--max-pods=1000"

# Como usuario SIN PRIVILEGIOS
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

source <(kubectl completion bash)
echo "source <(kubectl completion bash)" | tee -a ~/.bashrc

# Configuracion de calico
# https://docs.tigera.io/calico/latest/getting-started/kubernetes/quickstart
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.28.1/manifests/calico.yaml

kubectl taint nodes <node_name> node-role.kubernetes.io/control-plane-




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
apt install python3-pip python3-venv -y 
sudo apt install -y pkg-config libmysqlclient-dev
sudo apt install -y default-libmysqlclient-dev

git clone https://github.com/valdiviesod/kubepy -b dev






# Jenkins




