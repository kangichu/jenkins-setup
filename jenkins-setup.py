import subprocess
import os

def run_command(command, description):
    print(f"Executing: {description}")
    subprocess.run(command)
    print("Done.")

def create_jenkins_bridge_network():
    run_command(['docker', 'network', 'create', 'jenkins'], "Creating Jenkins bridge network")

def run_docker_dind_image():
    run_command(['docker', 'run', '--name', 'jenkins-docker', '--rm', '--detach',
                '--privileged', '--network', 'jenkins', '--network-alias', 'docker',
                '--env', 'DOCKER_TLS_CERTDIR=/certs',
                '--volume', 'jenkins-docker-certs:/certs/client',
                '--volume', 'jenkins-data:/var/jenkins_home',
                '--publish', '2376:2376', 'docker:dind'], "Running Docker-in-Docker image")

def create_dockerfile():
    dockerfile_content = '''FROM jenkins/jenkins:2.401.2-jdk17
    USER root
    RUN apt-get update && apt-get install -y lsb-release
    RUN curl -fsSLo /usr/share/keyrings/docker-archive-keyring.asc \\
    https://download.docker.com/linux/debian/gpg
    RUN echo "deb [arch=$(dpkg --print-architecture) \\
    signed-by=/usr/share/keyrings/docker-archive-keyring.asc] \\
    https://download.docker.com/linux/debian \\
    $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
    RUN apt-get update && apt-get install -y docker-ce-cli
    USER jenkins
    RUN jenkins-plugin-cli --plugins "blueocean docker-workflow"'''

    with open('Dockerfile', 'w') as dockerfile:
        dockerfile.write(dockerfile_content)

def build_docker_image():
    run_command(['docker', 'build', '-t', 'myjenkins-blueocean:2.401.2-1', '.'], "Building Jenkins Docker image")

def run_jenkins_container():
    run_command(['docker', 'run', '--name', 'jenkins-blueocean', '--restart=on-failure', '--detach',
                '--network', 'jenkins', '--env', 'DOCKER_HOST=tcp://docker:2376',
                '--env', 'DOCKER_CERT_PATH=/certs/client', '--env', 'DOCKER_TLS_VERIFY=1',
                '--volume', 'jenkins-data:/var/jenkins_home',
                '--volume', 'jenkins-docker-certs:/certs/client:ro',
                '--publish', '8080:8080', '--publish', '50000:50000',
                'myjenkins-blueocean:2.401.2-1'], "Running Jenkins container")

def get_jenkins_password():
    run_command(['docker', 'exec', 'jenkins-blueocean', 'cat', '/var/jenkins_home/secrets/initialAdminPassword'], "Retrieving Jenkins initial admin password")

def access_jenkins_container():
    print("Accessing Jenkins container terminal. You can run Jenkins CLI commands here.")
    os.system('docker exec -it jenkins-blueocean bash')

if __name__ == '__main__':
    create_jenkins_bridge_network()
    run_docker_dind_image()
    create_dockerfile()
    build_docker_image()
    run_jenkins_container()
    get_jenkins_password()
    # access_jenkins_container()
