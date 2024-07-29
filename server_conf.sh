# Instalacion y configuracion del servidor kubernetes en Ubuntu Server 24.04
# Configurar dns con netplan previamente
# Instalar microk8s en el proceso de configuracion o manualmente
# sudo snap install microk8s --classic
# git clone https://github.com/valdiviesod/kubepy -b dev
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg
# Reemplazar version del paquete segun la version actual
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
sudo chmod 644 /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo chmod 644 /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y kubectl
sudo snap alias microk8s.kubectl kubectl
mkdir $HOME/.kube
touch mkdir $HOME/.kube/.config
sudo microk8s.kubectl config view --raw > $HOME/.kube/config

# Configuracion de docker
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl -y
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
sudo systemctl enable docker
sudo systemctl start docker

# MySQL
sudo apt install mysql-server -y
sudo systemctl enable mysql
sudo systemctl start mysql
sudo mysql_secure_installation
sudo systemctl restart mysqld
# Configuracion de base de datos y permisos
# https://docs.vultr.com/how-to-install-mysql-on-ubuntu-24-04



# Configuracion de proyecto (Pruebas)
sudo apt install python3-pip python3-venv -y 
cd kubepy
mkdir .kube
rsync -avh ~/.kube/ ~/kubepy/.kube/

echo "Server Setup Complete"

