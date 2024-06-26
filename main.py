#Test kubernetes access
import kr8s

for node in kr8s.get("nodes"):
    print(node.name)