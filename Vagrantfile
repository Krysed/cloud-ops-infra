Vagrant.configure("2") do |config|
  # Jenkins
  config.vm.define "jenkins-server" do |jenkins|
    jenkins.vm.box = "generic/ubuntu2204"
    jenkins.vm.box_version = "4.3.12"
    jenkins.vm.hostname = "jenkins-server"
    
    jenkins.vm.network "private_network", ip: "192.168.56.10"
    jenkins.vm.network "forwarded_port", guest: 8080, host: 8080
    
    jenkins.vm.synced_folder "./jenkins_data", "/srv/jenkins_data"
    
    # Ansible playbook for setting up the jenkins server
    jenkins.vm.provision "ansible" do |ansible|
      ansible.playbook = "playbooks/provision.yml"
    end
  end
end
