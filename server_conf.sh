# Instalacion y configuracion del servidor kubernetes en Debian 12
apt install sudo git
# git clone https://github.com/valdiviesod/kubepy -b dev
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

sudo swapoff -a
nano /etc/fstab # comment out the swap line

# Bridge de interfaz de red
cat <<EOF | tee /etc/modules-load.d/containerd.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter

cat <<EOF | tee /etc/sysctl.d/99-kubernetes-k8s.conf
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-ip6tables = 1
EOF

sudo sysctl --system

# Configuracion de docker
# Add Docker's official GPG key:
apt-get update
apt-get install ca-certificates curl -y
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update

apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y

# Instalacion de containerd
#apt update
#apt install -y containerd

#containerd config default > /etc/containerd/config.toml

#nano /etc/containerd/config.toml

# Cambiar a true: [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options] SystemdCgroup = false

#systemctl enable containerd
#systemctl restart containerd

# Instalacion de herramientas Kubernetes
# Guia: https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/
apt install gnupg gnupg2 curl software-properties-common -y
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmour -o /etc/apt/trusted.gpg.d/cgoogle.gpg
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list

apt update
apt install kubelet kubeadm kubectl -y
sudo apt-mark hold kubelet kubeadm kubectl
sudo systemctl enable --now kubelet

# Ignorar errores de preflight por paquetes que ya existen
sudo kubeadm init --pod-network-cidr=192.168.0.0/16 --ignore-preflight-errors=all
#sudo kubeadm init --pod-network-cidr=192.168.0.0/16 --ignore-preflight-errors=all --kubelet-extra-args="--max-pods=1000"

# Como usuario SIN PRIVILEGIOS
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

source <(kubectl completion bash)
echo "source <(kubectl completion bash)" | tee -a ~/.bashrc

# Configuracion de calico
# https://docs.tigera.io/calico/latest/getting-started/kubernetes/quickstart
kubectl apply -f https://docs.projectcalico.org/manifests/calico.yaml
kubectl get pods -n kube-system

# Configuracion de single node
#kubectl get nodes
#kubectl get nodes -o json | jq '.items[].spec.taints'
#kubectl taint node <nodename> node-role.kubernetes.io/control-plane:NoSchedule-

# Probar
#kubectl get nodes -o json | jq '.items[].spec.taints'
#kubectl get pods -n kube-system


# MySQL
# Ultima version repo mysql
# https://dev.mysql.com/downloads/repo/apt/
wget https://dev.mysql.com/get/mysql-apt-config_0.8.30-1_all.deb
dpkg -i mysql-apt-config_0.8.30-1_all.deb
apt update
apt install mysql-server -y
systemctl enable mysql
systemctl start mysql
mysql_secure_installation
# Configurar base de datos y permisos


# Configuracion de proyecto (Pruebas)
apt install python3-pip python3-venv -y 
cd kubepy
mkdir .kube
rsync -avh ~/.kube/ ~/kubepy/.kube/

# Configurar firewall


