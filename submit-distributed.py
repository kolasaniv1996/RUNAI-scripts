import json
import requests
import sys

# Configuration
ClientName = "your client name"
AppSecret = "YOUR AppSecret"
Realm = "runai"
base_url = "YOUR base_url"

def get_bearer_token():
    login_payload = f"grant_type=client_credentials&client_id={ClientName}&client_secret={AppSecret}"
    login_headers = {"content-type": "application/x-www-form-urlencoded"}
    response = requests.post(f"{base_url}/auth/realms/{Realm}/protocol/openid-connect/token", 
                             headers=login_headers, data=login_payload)
    return response.json()['access_token']

def create_distributed_workload(workload_name, cluster_id, gpu_amount, image):
    url = f"{base_url}/researcher/api/v1/workloads/distributed"
    
    if gpu_amount < 1:
        gpu_request_type = "portion"
        gpu_portion_request = gpu_amount
        gpu_devices_request = None
    else:
        gpu_request_type = "count"
        gpu_portion_request = None
        gpu_devices_request = int(gpu_amount)

    payload = {
        "name": workload_name,
        "useGivenNameAsPrefix": True,
        "projectId": "1",
        "clusterId": cluster_id,
        "spec": {
            "command": "python3",
            "args": "/opt/pytorch-mnist/mnist.py --epochs=1",
            "image": image,
            "imagePullPolicy": "Always",
            "createHomeDir": True,
            "nodePools": ["default"],
            "terminateAfterPreemption": False,
            "autoDeletionTimeAfterCompletionSeconds": 15,
            "backoffLimit": 3,
            "compute": {
                "gpuRequestType": gpu_request_type,
                "gpuPortionRequest": gpu_portion_request,
                "gpuDevicesRequest": gpu_devices_request
            },
            "security": {
                "allowPrivilegeEscalation": False,
                "uidGidSource": "fromTheImage",
                "seccompProfileType": "RuntimeDefault",
                "runAsNonRoot": True,
                "hostIpc": False,
                "hostNetwork": False,
                "readOnlyRootFilesystem": False
            },
            "numWorkers": 1,
            "distributedFramework": "PyTorch"
        }
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_bearer_token()}"
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python script.py <workload_name> <cluster_id> <gpu_amount> <image>")
        sys.exit(1)

    workload_name = sys.argv[1]
    cluster_id = sys.argv[2]
    gpu_amount = float(sys.argv[3])
    image = sys.argv[4]

    response = create_distributed_workload(workload_name, cluster_id, gpu_amount, image)

    if response.status_code == 202:
        print("Distributed workload creation request accepted.")
        workload_id = response.json()["workloadId"]
        print("Workload ID:", workload_id)
    else:
        print("Failed to create distributed workload.")
        print("Status Code:", response.status_code)
        print("Response:", response.text)
