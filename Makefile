
check-env-%:
	@ if [ "${${*}}" = "" ]; then \
			echo "Environment variable $* not set"; \
			exit 1; \
	fi

clean:
	rm -rf venv/
	find . -name __pycache__ -exec rm -rf {} \;

venv:
	python3 -m venv venv
	. venv/bin/activate
	pip3 install -r etc/webserver_requirements.txt

full: check-env-target
	rsync --progress -rv --exclude=__pycache__ --exclude=.git --exclude=venv  ../dns_admin/ ${target}:dns_admin/
	ssh ${target} cd dns_admin \&\& buildah bud -f Dockerfile -t overlord-dns-admin

test: check-env-target
	rsync --progress -rv cgi-bin/*.py ${target}:dns_admin/cgi-bin/
	rsync --progress -rv etc/ ${target}:dns_admin/etc/
	ssh ${target} cd dns_admin \&\& podman run -d --replace  --name=dns-admin --env-file=./etc/envfile --net=host -v ./cgi-bin/dns_server.py:/cgi-bin/dns_server.py -v ./etc/config.ini:/etc/config.ini localhost/overlord-dns-admin
