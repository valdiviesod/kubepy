# Instalacion y configuracion del servidor kubernetes en Debian 12
# git clone https://github.com/valdiviesod/kubepy -b dev
# Configurar red primero
# Guia: https://reintech.io/blog/configuring-network-interfaces-debian-12
# Ejecutar comandos como root

# Configuracion de Kubernetes
# Guia: https://www.bentasker.co.uk/posts/documentation/linux/building-a-k8s-cluster-on-debian-12-1-bookworm.html 
# Puertos: TCP/6443: The port used by the Kubernetes API server
# TCP/2379-2380: Used by the etcd API
# TCP/10250: The Kubelet API
# TCP/10257: Kube Controller Manager (see note below)
# TCP/10259: Kube scheduler (see note below)
# TCP/30000-32767: Nodeport services

swapoff -a
nano /etc/fstab # comment out the swap line

# Bridge de interfaz de red
cat <<EOF | tee /etc/modules-load.d/containerd.conf
overlay
br_netfilter
EOF

modprobe overlay
modprobe br_netfilter

cat <<EOF | tee /etc/sysctl.d/99-kubernetes-k8s.conf
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-ip6tables = 1
EOF

sysctl --system

# Instalacion de containerd
apt update
apt install -y containerd

containerd config default > /etc/containerd/config.toml

nano /etc/containerd/config.toml

# Cambiar a true: [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options] SystemdCgroup = true

systemctl enable containerd
systemctl restart containerd

# Instalacion de Kubernetes
apt install gnupg gnupg2 curl software-properties-common -y
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmour -o /etc/apt/trusted.gpg.d/cgoogle.gpg
apt-add-repository "deb http://apt.kubernetes.io/ kubernetes-xenial main"

apt update
apt install kubelet kubeadm kubectl -y

apt-mark hold kubelet kubeadm kubectl

kubeadm init --control-plane-endpoint=$HOSTNAME

# Como usuario SIN PRIVILEGIOS
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

source <(kubectl completion bash)
echo "source <(kubectl completion bash)" | tee -a ~/.bashrc

# Calico para la administracion de red
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.26.1/manifests/calico.yaml

# Configuracion de single node
kubectl get nodes
kubectl get nodes -o json | jq '.items[].spec.taints'
kubectl taint node <nodename> node-role.kubernetes.io/control-plane:NoSchedule-

# Probar
kubectl get nodes -o json | jq '.items[].spec.taints'
kubectl get pods -n kube-system


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


