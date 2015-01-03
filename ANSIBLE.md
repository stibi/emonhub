# emonHub installation with Ansible

## Why

* velké zjenodušení instalace 
* nováček může mít funkční emonHub během chvilky, nemusí řešit detaily instalace
* instalace je zdokumentovaná
* proces instalace je reprodukovatelný
* není třeba emonhub-dev
* celé je to "more solid"

## You need Ansible

Nejdřív velmi krátce představím co je Ansible, pokud jste o tomto nástroji ještě neslyšeli. Z toho by mělo vyplynout, proč je velmi dobrý nápad použít Ansible nepříklad pro instalaci emonHub. 

Ansible je nástroj pro automatizaci. Pomocí čitelné YAML syntaxe dovoluje popsat všechny jednotlivé kroky nutné pro instalaci a konfiguraci služby, systému, aplikace, ať už na jednom stroji, clusteru, nebo velkých skupinách strojů a serverů.

Každý Ansible `task` je malá součást většího celku, může to být vytvoření souboru, rozbalení archivu, nainstalovaní balíčku, spuštění service a tak dále. Tyto tasky je možno sloučit do jednoho celku, kterému se říká role. Takové role se pak dá přiřadit určitému stroji/serveru, říkám tak, že nějaký server má tuto roli a proto na něj Ansible aplikuje všechny tasky, která tato role předepisuje, konkrétně když Ansible řeknu, že server `raspi` má mít roli `emonhub-ansible-role`, Ansible na `raspi` spustí všechny tasky z této role, takže na konci mám server `raspi` s funkčním emonHub.

Ansible nepotřebuje žádnou klientskou část, nic cílovém stroji se nemusí instalovat nic navíc, stačí, když je tam python2 a funkční SSH. Ansible je client-less.

Výhody jsou opakovatelnost celé procedury, kompletní konfiguraci každého serveru můžu kdykoli spustit znovu, vše je takto taky zdokumentované, nemusím vzpomínat, co jsem kde a jak udělal, kdykoli si to můžu jednoduše zjistit a když mi náhodou moji konfiguraci server někdo ručně pokazí, Ansible zase všechno dá do pořádku.

## How to install Ansible

Všechny distribuce Linuxu (aspoň ty nejznámější určitě) májí někde v repozitářích balíček s Ansible, takže nejlepší nápad bude asi použít váš balíčkovací systém.

Všechny detaily jsou popsány v [dokumentaci](http://docs.ansible.com/intro_installation.html).

## How to use Ansible

Jako první je potřeba inventory file, to je soubor který popisuje všechny servery a skupiny serverů, na které se aplikuje Ansible playbook a jednotlivé role a tasky.

V tomto ukázkovém případě, inventory obsahuje jen jednu skupinu s jedním strojem, který je Raspberry Pi. Uložte do souboru třeba pod názvem `inventory`:

```
[raspi]
192.168.2.134 ansible_connection=ssh ansible_python_interpreter=/usr/bin/python2 ansible_ssh_user=ansible ansible_ssh_port=2244
```

První věc je IP adresa, potom následuje několik parametrů, nejsou povinné. V mém případě, kdy na Raspberry Pi je nainstalovaný Archlinux, musím Ansible poradit, kde je tam binárka s Python 2, který Ansible používá. Na stroj se Ansible připojí přes uživatele `ansible` (ssh public key authentication se pro tohoto uživatele hodí, sudo stejně tak) a SSH spojení se vytvoří na portu `2244`.

S inventory file už se něco dá dělat, třeba toto může být něco jako hello world pro Ansible:

```
$ ansible -i inventory raspi -m ping
192.168.2.134 | success >> {
    "changed": false, 
    "ping": "pong"
}
```

Parametrem `-i` Ansible říkám, který inventory soubor použít, parametrem `-m` říkám, který [Ansible module](http://docs.ansible.com/modules.html) použít na všechny stroje ve vybraném inventory souboru.

Možností je více, toto byl ten nejjednodušší možný příklad.

Další krok je Ansible `playbook`, který popisuje sled úkolů/rolí, jeden za druhým, které se provedou na strojích specifikovaných v `inventory` souboru.

Všechny kroky potřebné k nainstalování a konfiguraci emonHub na Raspberry Pi jsou sloučeny do role, kterou je možno přiřadit konkrétnímu stroji a dokonce jí nastavit několik parametrů, podle vlastní potřeby.

## How to use emonHub Ansible role

Ansible playbook pro instalaci emonHub může vypadat následovně:

main.yml:
```
---
- name: Configure my RaspberryPi
  hosts: raspi
  roles:
    - { role: emonhub-ansible-role, rfm12pi_group: 210, rfm12pi_freq: 868,rfm12pi_baseid: 1, emonhub_emoncms_apikey: "6a272ec63787809a59e4f56bfaac4f3b" }
```

Samozřejmě, můžete přiřadit další role, ideálně tak pokrýt kompletní konfiguraci. [Já to tak dělám](https://github.com/stibi/etc/blob/master/playbooks/main.yml), funguje to moc dobře a vyplatí se to, doporučuji.

TODO neklonovat z gitu, použít ansible galaxy
Samotnou roli naklonujte z gitu do adresáře `roles`, který je na stejné úrovni jako soubor `main.yml` a `inventory` soubor.

TODO tohle jde udelat ansible prikazy, ne? Nejaky init, galaxy install a tak...

    $ mkdir roles
    $ cd roles
    $ git clone 


Souborová struktura tedy vypadá nasledovně:
```
TODO
```

Poslední krok je spuštění našeho Ansible playbooku. Tímto příkazem:

```
ansible-playbook -i inventory main.yml
```

TODO výpis? zmínit cowsay a jak to vypnout?

Ansible provede postupně všechny tasky, na konci by měl být funkční emonHub nainstalovaný na Raspberry Pi.

## Configuration of the role

TODO

## Support

Toto všechno je momentalně vyzkoušeno a provozováno na Raspberry Pi a Archlinux ARM jako operační systém. Samozřejmě podpora pro Raspbian je nutnost, většina Rapsberry Pi má nejspíš nainstalovaný Raspbian.

V Ansible toto není problém. Je jen potřeba vyřešit několik detailů. Například názvy balíčků se závislostmi jsou jiné, lehce řešitelné, v `vars/` je YAML soubor pro Archlinux a Raspbian, který obsahuje proměnné které jsou distro specific, jako třeba seznam balíčků.

Další rozdíl je init systém. Na Archlinuxu je to systemd, na Raspbianu SysV. Opět lehce řešitelné, to jestli se konkrétní task spustí nebo ne je možno ovlivnit:

    when: ansible_distribution == "Raspbian"

Task s takovou direktivou se spustí pouze na Raspbianu. V případě init souboru pro systemd, v `tasks/main.yml` jsou dva různé tasky, jeden vytvoří systemd službu, druhý sysv službu, jeden se spustí pouze na Archlinuxu, druhý pouze na Raspbianu.

Největší problém tedy aktuálně je, že jsem instalaci emonHub pomocí Ansible zatím neotestoval nikde jinde krom mého vlastního Raspberry Pi s Archlinuxem. Jakmile budu mít Raspberry Pi navíc, udělám víc testů, nebo i dříve, třeba na virtualizovaném systému, každopádně pomoc by se mi tady hodila.
