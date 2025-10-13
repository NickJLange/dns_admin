.DEFAULT_GOAL := all

include private/dns_servers

VERSION=2.0

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
	   uv venv; \
	   source venv/bin/activate ; \
	   uv pip install -r etc/webserver_requirements.txt ; \
	fi

full: venv
	cp private/etc/config.ini etc/config.ini
	cp private/dns_servers  etc/dns_servers
	cp private/etc/envfile etc/envfile
	( \
        . venv/bin/activate; \
    	pyclean .; \
    	podman build -f Containerfile  . \
	)

push:
	podman tag localhost/overlord-dns-admin:latest ghcr.io/nickjlange/overlord-network-kill-switch:${VERSION}-test
	podman push ghcr.io/nickjlange/overlord-network-kill-switch:${VERSION}-test

push-local: check-env-target
	rsync --progress -rv cgi-bin/*.py ${target}:dns_admin/cgi-bin/
	rsync --progress -rv etc/ ${target}:dns_admin/etc/
	ssh ${target} cd dns_admin \&\&

TEST_CMD = podman run -d --replace --name=overlord-dns -p 19000:19000 --env-file=./etc/envfile --dns=${DNS_SERVERS} -v ./cgi-bin/:/opt/webserver/cgi-bin/ -v ./lib/:/opt/webserver/lib/  -v ./etc/config.ini:/opt/webserver/etc/config.ini

test-local:
	$(TEST_CMD) localhost/overlord-dns-admin

test-remote:
	podman pull ghcr.io/nickjlange/overlord-network-kill-switch:${VERSION}-test
	$(TEST_CMD) ghcr.io/nickjlange/overlord-network-kill-switch:${VERSION}-test
test-remote:

test:

all:
	@echo "No op."
