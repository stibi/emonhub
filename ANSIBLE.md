# emonHub installation with Ansible

## You need Ansible

First of all just shortly about what is Ansible, if you have not heard of it yet. That should also imly why it's a very good idea to use Ansible for example to install emonHub.

Ansibl is an automation too. With a simple, human readable YAML syntaxe, it allows to describe each and all steps required to install and configure a servuce, or a system, an application, on a single machine, or a cluster or a big infrastructure composed of different groups and machines and servers.

Each Ansible `task` is just a small piece of a bigger unit, it could a task to create a file, extract an archive, install a package, enable and start a service and so on…
More tasks with the same context could be grouped to a role. Then you can assign a role(s) to a specific host, you are saying that this host has this role and so Ansible applies all tasks that role described on this specific host or hosts.

Ansible doesn't need a client/host side, no need to install anything extra, just a python2 installation and working SSH connection to the host(s). Ansible is clientless.

## Why to use Ansible for the installation

* the installation get a lot of easier
* a newcomer to the project could be up and running in just a moment, without bothering about installation details
* the installation process is well documented for free
* the installation process is reproducible anytime
* no need for the emonhub-dev repository with the script
* it's "more solid" and reliable
* documentation again - you don't have to remember some specific details, just check the Ansible description
* easy to fix some mistake done by someone manually on the host - you just run the Ansible playbook again againt the host and it's fixed, consistent again

## How to install Ansible

All Linux distributions (or at least the biggest ones for sure) offers a package with Ansible in their repositories. The best idea is to use your package manager to install Ansible.

You can check for more details in [documentation](http://docs.ansible.com/intro_installation.html).

## How to use Ansible

First we need a `inventory` file, that's a file which describes all the server and group of server, which are managed by Ansible, on which are the playbook and all its roles and tasks applied.

In this example case, the `inventory` contains only one group with one host, which is a Raspberry Pi machine. Save to a file called "inventory":

```
[raspi]
192.168.2.134 ansible_connection=ssh ansible_python_interpreter=/usr/bin/python2 ansible_ssh_user=ansible ansible_ssh_port=2244
```

So we have a group called "raspi", with one host, specified by its IP address and the few of parameters, not required, but usefull.

In my case, I have Archlinux ARM installed on the Raspberry Pi, so I have to help Ansible to find a binary with Python 2, which is needed for Ansible. For the connection is used an user called `ansible` (ssh public key authentication is very handy here, sudo as well) and also a port `2244` is used for the connection.

Now when we have the `inventory` file, we can do something actually. This is kind of a hello world example for Ansible:

```
$ ansible -i inventory raspi -m ping
192.168.2.134 | success >> {
    "changed": false, 
    "ping": "pong"
}
```

The argument `-i` specifies the `inventory` file to be use, the argument `-m` specifies which [Ansible module](http://docs.ansible.com/modules.html) to execute on all hosts defined in the `inventory` file.

This is just the simplest possible example, you can much complex thing than that.

The next step is Ansible `playbook`, which describes a sequence of tasks and roles, one after another, all executed on hosts specified in the `inventory` file.

All steps needed to install and configure emonHub on Raspberry Pi are grouped into a role, which you can assign to a specific host(s), this role is parametrized, so you can specify few of the key properties for the installation, you will in the example below.

## How to use emonHub Ansible role

The Ansible playbook for emonHub installation could look like this:

main.yml:
```
---
- name: Configure my RaspberryPi
  hosts: raspi
  roles:
    - { role: emonhub-ansible-role, rfm12pi_group: 210, rfm12pi_freq: 868,rfm12pi_baseid: 1, emonhub_emoncms_apikey: "6a272ec63787809a59e4f56bfaac4f3b" }
```

Of course, you can assign more different roles to a host and ideally cover the complete configuration of the host. [I'm doing this](https://github.com/stibi/etc/blob/master/playbooks/main.yml), it's working very well and it's worth it, I can recommend.

TODO don't clone the role from git, use ansible galaxy
TODO is it possible to boostrap with ansible? some "init" or something like that?

    $ mkdir roles
    $ cd roles
    $ git clone 


The directory and file structure should look like this:
```
TODO
```

The last step is to run the playbook. Use the following command:

```
ansible-playbook -i inventory main.yml
```

TODO output? mention cowsay and how to turn it off?

Ansible will execute all the task for the role and you should end up with working emonHub installed on the Raspberry Pi.

## Configuration of the role

TODO

## Support

Currently all of this is tested, used and maintained on a Raspberry Pi with Archlinux ARM as operating system. Of course, support for Raspbian is a must, because I guess most of the Raspberry Pi machines have Raspbian installed.

And this is not a problem for Ansible. Just a few details needs to taken care of. For example, names of the packages with dependencies for emonHub. These are different for each distribution. Easy to solve, just have a look to `vars/`, you find two YAML files, one for Archlinux, another for Raspbian, each one contains distribution specific properties, like the list of packages.

Another different is a init system. Systemd for Archlinux, SysV for Raspbian. Easy again, you can specify if a task is run or not under some condition:

    name: "This is task for Raspbian only"
    command: echo "I'm Raspbian!"
    when: ansible_distribution == "Raspbian"

As you can guess, with this directive, the task is applies only on hosts with Raspbian. So for the init system, take a look to the `tasks/main.yml`, you will find two different tasks for installing the init for emonhub, one creates a systemd service, the second SysV service.

Actually the biggest problem right now is that I have not tested the installation & configuration on Raspbian, only my own Raspberry Pi with Archlinux.
Once I have another Raspberry Pi for spare, I'll do more tests for Raspbian and possible other systems too (recommendations?). Or I can use virtualization maybe, let's see. But help would be really appreciated here. Thanks!
