# Create test pod
from kr8s.objects import Pod

# Generate a simple Pod spec using the `nginx` container image
pod = Pod.gen(name="webserver", image="nginx:latest", ports=[80])  
# Create the Pod
pod.create()  

# Test kubernetes access
import kr8s

for node in kr8s.get("nodes"):
    print(node.name)