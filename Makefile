.DEFAULT_GOAL := all

include dns_servers

check-env-%:
	@ # This code checks if an environment variable is empty
	@ # set ahead of running makefile. i.e. target=blah make check-env-target
	@ if [ "${${*}}" = "" ]; then \
			echo "Environment variable $* not set"; \
			exit 1; \
	fi

clean:
	rm -rf venv/
	find . -name __pycache__ -exec rm -rf {} \;

venv:
	if [ ! -d "venv" ] ; then \
	   python3 -m venv venv ; \
	   . venv/bin/activate ; \
	   pip3 install -r etc/webserver_requirements.txt ; \
	fi

full: venv
	( \
        . venv/bin/activate; \
    	pyclean .; \
    	podman build -f Containerfile -t overlord-dns-admin . \
	)

push: check-env-target
	rsync --progress -rv cgi-bin/*.py ${target}:dns_admin/cgi-bin/
	rsync --progress -rv etc/ ${target}:dns_admin/etc/
	ssh ${target} cd dns_admin \&\&

test:
#	rsync --progress -rv cgi-bin/*.py ${target}:dns_admin/cgi-bin/
#	rsync --progress -rv etc/ ${target}:dns_admin/etc/
#	ssh ${target} cd dns_admin \&\&
	podman run -d --replace --name=overlord-dns -p 19000:19000 --env-file=./etc/envfile --dns=${DNS_SERVERS} -v ./cgi-bin/:/opt/webserver/cgi-bin/ -v ./lib/:/opt/webserver/lib/  -v ./etc/config.ini:/opt/webserver/etc/config.ini localhost/overlord-dns-admin

all:
	@echo "No op."
