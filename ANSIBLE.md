# emonHub installation with Ansible

## You need Ansible

First of all, shortly about what is Ansible, in the case you have not heard of it yet. That should also imply why it's very good idea to use Ansible for example to install emonHub.

Ansible is an automation tool. Similar to chef or puppet. With simple, human readable YAML syntax, it allows to describe each and all steps required to install and configure a service, or a system, an application, on a single machine, or a cluster or a big infrastructure composed of different groups and machines and servers. The idea is that you don't have to do all the job manually, just write all the instructions in a Ansible "playbook" so Ansible understand it, and then just run the playbook.

Each Ansible `task` is just a small piece of a bigger unit, it could be a task to create a file, extract an archive, install a package, enable and start a service and so on…See what's is needed to install emonHub, Ansible [can](http://docs.ansible.com/modules_by_category.html) do all of that.
More tasks with the same context could be grouped to a role. Then you can assign a role(s) to a specific host, you are saying that this host has this role and so Ansible applies all tasks that role contains on this specific host or hosts.

Ansible doesn't need any client application on the host side, no need to install anything extra, just python2 and working SSH connection on the host(s). Ansible is clientless.

## Why to use Ansible for the emonhub installation

* the installation get a lot of easier
* a newcomer to the project could be up and running in just a moment, without bothering about the installation details
* the installation process is well documented for free
* the installation process is reproducible anytime
* no need for the emonhub-dev repository, no bash scripting
* it's "more solid" and reliable
* documentation again - you don't have to remember some specific details, just look it up in the Ansible YAML tasks file
* easy to fix some mistake done by someone manually on the host - you just run the Ansible playbook again against the host and it's fixed and consistent again

## How to install Ansible

All Linux distributions (or at least the biggest ones for sure) offers a package with Ansible in their repositories. The best idea is to use your package manager to install Ansible.

You can check for more details in [documentation](http://docs.ansible.com/intro_installation.html).

## How to use Ansible

First we need a `inventory` file, that's a file which describes all the hosts and groups of hosts, which are managed by Ansible. So you can reffere to them and assign different roles and tasks to them.

In this example case, the `inventory` contains only one group with one host, which is a Raspberry Pi machine. Save to a file called "inventory":

```
[raspi]
192.168.2.134 ansible_connection=ssh ansible_python_interpreter=/usr/bin/python2 ansible_ssh_user=ansible ansible_ssh_port=2244
```

So we have a group called "raspi", with one host, specified by its IP address and few of parameters, not required, but useful.

In my case, I have Archlinux ARM installed on the Raspberry Pi, so I have to help Ansible to find the binary with Python 2, which is needed for Ansible. For the connection is used an user called `ansible` (ssh public key authentication is very handy here, sudo as well) and the port `2244` is used for a connection.

Now, when we have the `inventory` file, we can do something actually. This is kind of a hello world example for Ansible:

```
$ ansible -i inventory raspi -m ping
192.168.2.134 | success >> {
    "changed": false, 
    "ping": "pong"
}
```

The argument `-i` specify path to the `inventory` file, the argument `-m` specify which [Ansible module](http://docs.ansible.com/modules.html) to execute on all hosts defined in the `inventory` file.

This is just the simplest possible example, you can much more complex things than that.

The next step is an Ansible `playbook`, which describes a sequence of tasks and roles, one after another, all executed on the hosts specified in the `inventory` file.

All the needed steps  to install and configure emonHub on a Raspberry Pi are grouped into a role, which you can assign to a specific host(s), this role is parametrized, so you can specify few of the key properties for the installation, you will see in the example below.

## How to use emonHub Ansible role

You should have the `inventory` file described above, now create new directory for roles and install there the `emonhub-ansible-role`. You can do that simply by cloning the role from [github repository](https://github.com/stibi/emonhub-ansible-role), or you can install it with [Ansible Galaxy](https://galaxy.ansible.com/) (roles repository).

    $ mkdir roles
    $ ansible-galaxy install -p roles martin.stiborsky.emonhub-ansible-role

Now, create the Ansible playbook. Create a new file, `main.yml` with following content:

```
---
- name: Configure my RaspberryPi
  hosts: raspi
  roles:
    - role: martin.stiborsky.emonhub-ansible-role
      rfm12pi_group: 210
      rfm12pi_freq: 868
      rfm12pi_baseid: 1
      emonhub_emoncms_apikey: "6a272ec63787809a59e4f56bfaac4f3b"
```

Of course, you can assign more different roles to a host and ideally cover the complete configuration of a host. [I'm doing this](https://github.com/stibi/etc/blob/master/playbooks/main.yml), it's working very well and it's worth it, I can recommend.

The directory and file structure now should look like this:

```
.
├── main.yml
└── roles
    └── martin.stiborsky.emonhub-ansible-role
        ├── defaults
        │   └── main.yml
        ├── handlers
        │   └── main.yml
        ├── meta
        │   └── main.yml
        ├── README.md
        ├── tasks
        │   └── main.yml
        ├── templates
        │   ├── emonhub.conf.j2
        │   ├── emonhub.systemd.service.j2
        │   ├── emonhub.sysv.defaults.j2
        │   └── emonhub.sysv.service.j2
        └── vars
            ├── Archlinux.yml
            ├── main.yml
            └── Raspbian.yml
```

The last step is to run the playbook. Use the following command:

```
ansible-playbook -i inventory main.yml
```

NOTE: maybe you are now surprised with cows:

![Ansible cows](https://dl.dropboxusercontent.com/u/3189942/pics/cowsay_shot.png)

Don't worry, you can [turn it off](http://docs.ansible.com/faq.html#how-do-i-disable-cowsay).

Ansible will execute all the task from the role and you should end up with working emonHub, installed on a Raspberry Pi.

## Configuration of the role

You can configure some of the role parameters, if you like.

When you define the role for a host, you can setup few key parameters (see the example above):

`rfm12pi_group` : the network group for RFM12B modules communication (if not specified, the default is 210)

`rfm12pi_freq` : the frequency on which RFM12B modules communicates (if not specified, the default is 868)

`fm12pi_baseid` : the base ID of a RFM12Pi module on your raspi (if not specified, the default is 1)

`emonhub_emoncms_apikey` : the apikey for communication with EmonCMS (no default value, must be specified)

For more configuration options, you can take a look to `vars/*.yml`.

## Support

Currently, all of this is tested, used and maintained on my Raspberry Pi with Archlinux ARM as operating system. Of course, support for Raspbian is a must, because I guess most of the Raspberry Pi machines got Raspbian installed.

This is not a problem for Ansible. Just a few details needs to taken care of. For example, names of the packages with dependencies for emonHub. These are different for each distribution. Easy to solve, just have a look to `vars/`, you find two YAML files, one for Archlinux, another for Raspbian, each one contains distribution specific properties, like the list of packages.

Another difference is the init system. Systemd for Archlinux, SysV for Raspbian. Easy again, you can specify if a task is run or not under some condition:

    name: "This is task for Raspbian only"
    command: echo "I'm Raspbian!"
    when: ansible_distribution == "Raspbian"

As you can guess, with this directive, the task is applied only on hosts with Raspbian. So, for the init system, take a look to the `tasks/main.yml`, you will find two different tasks for installing the init for emonhub, one creates  systemd service, the second SysV service.

Actually the biggest problem right now is that I have not tested the installation & configuration on Raspbian, only on my own Raspberry Pi with Archlinux.

Once I have another Raspberry Pi for spare, I'll do more tests for Raspbian and possibly other systems too (recommendations?). Or I can use virtualization maybe, let's see. But help would be really appreciated here. Thanks!
