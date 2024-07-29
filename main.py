# Create test pod
from kr8s.objects import Pod

# Generate a simple Pod spec using the `nginx` container image
pod = Pod.gen(name="webserver", image="nginx:latest", ports=[80])  
# Create the Pod
pod.create()  

# Test kubernetes access
import kr8s

for node in kr8s.get("nodes"):
    print("Node name:" , node.name)

for pod in kr8s.get("pods", field_selector="status.phase=Running"):
    print("Pod names:", pod.name)