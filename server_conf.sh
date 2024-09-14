# Instalacion y configuracion del servidor kubernetes en Debian 12
# Entornos de desarrollo
sudo apt install sudo git curl jq -y
curl -fsSL https://deb.nodesource.com/setup_22.x -o nodesource_setup.sh
sudo bash nodesource_setup.sh
sudo apt-get install -y nodejs
sudo apt install python3-pip python3-venv -y 
sudo apt install -y pkg-config 
sudo apt install -y default-libmysqlclient-dev
node -v

# Configurar red 
# Guia: https://reintech.io/blog/configuring-network-interfaces-debian-12

# Sudo

# Configuracion de Kubernetes
# Puertos: TCP/6443: The port used by the Kubernetes API server
# TCP/2379-2380: Used by the etcd API
# TCP/10250: The Kubelet API
# TCP/10257: Kube Controller Manager (see note below)
# TCP/10259: Kube scheduler (see note below)
# TCP/30000-32767: Nodeport services

swapoff -a
nano /etc/fstab # comment out the swap line

cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.ipv4.ip_forward = 1
EOF

sudo bash

apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

curl -fsSL https://download.docker.com/linux/debian/gpg |  gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" |  tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install docker-ce docker-ce-cli containerd.io -y

docker info

cat <<EOF |  tee /etc/modules-load.d/containerd.conf
overlay
br_netfilter
EOF


modprobe overlay
modprobe br_netfilter


cat <<EOF | tee /etc/sysctl.d/99-kubernetes-cri.conf
net.bridge.bridge-nf-call-iptables  = 1
net.ipv4.ip_forward                 = 1
net.bridge.bridge-nf-call-ip6tables = 1
EOF

sysctl --system

mkdir -p /etc/containerd
containerd config default | tee /etc/containerd/config.toml

systemctl restart containerd

cp /etc/containerd/config.toml /etc/containerd/config.toml-orig
# Edit the /etc/containerd/config.toml file with this: https://readthedocs.vinczejanos.info/Blog/2021/09/25/Install_Single_Node_Kubernetes_Cluster/
# [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
# SystemdCgroup = true

VERSION="v1.30.0" # check latest version in /releases page
wget https://github.com/kubernetes-sigs/cri-tools/releases/download/$VERSION/crictl-$VERSION-linux-amd64.tar.gz
sudo tar zxvf crictl-$VERSION-linux-amd64.tar.gz -C /usr/local/bin
rm -f crictl-$VERSION-linux-amd64.tar.gz

# Fix "crictl ps" command error (opcional)
cat <<EOF > /etc/crictl.yaml
runtime-endpoint: unix:///run/containerd/containerd.sock
image-endpoint: unix:///run/containerd/containerd.sock
timeout: 2
debug: false
pull-image-on-create: false
EOF



# Instalacion de herramientas Kubernetes
cat <<EOF |  tee /etc/modules-load.d/k8s.conf
br_netfilter
EOF

cat <<EOF |  tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-ip6tables = 1
net.bridge.bridge-nf-call-iptables = 1
EOF

sysctl --system

apt-get update
apt-get install -y apt-transport-https ca-certificates curl

curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.31/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
#Opcional
sudo systemctl enable --now kubelet

kubeadm version -o yaml
sudo reboot now 

#Revisar que no haya overlap de IPs
#kubeadm init \
#--cri-socket unix:///var/run/containerd/containerd.sock \
#--service-cidr 10.22.0.0/16 \
#--pod-network-cidr 10.23.0.0/16

sudo kubeadm init --pod-network-cidr=10.244.0.0/16

# Mirar siempre ultima version
kubectl apply -f https://github.com/weaveworks/weave/releases/download/v2.8.1/weave-daemonset-k8s.yaml

kubectl get pods --all-namespaces -o wide

kubectl get nodes -o wide

kubectl label node kubepy node-role.kubernetes.io/worker=

kubectl taint nodes kubepy node-role.kubernetes.io/control-plane-

kubectl edit -n kube-system deployment coredns
#Change replicas to 1

kubectl -n kube-system get pods

#kubectl run nginx-test-pod --image=nginx --port=80
# Install Nginx Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.11.2/deploy/static/provider/cloud/deploy.yaml

# Wait for Nginx Ingress Controller to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s

# Create a namespace for your application (if not using default)
kubectl create namespace myapp

# Create a ConfigMap for Nginx configuration (optional, for custom settings)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-configuration
  namespace: ingress-nginx
data:
  proxy-body-size: "10m"
  proxy-connect-timeout: "10"
EOF


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





