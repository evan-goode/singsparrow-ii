default: all

all:
	./setup.py build

install:
	./setup.py install
	install -m 644 singsparrow-ii.service /usr/lib/systemd/system/
	install -m 644 singsparrow-ii.toml /etc/singsparrow-ii.toml
	systemctl daemon-reload
	systemctl status singsparrow-ii.service --no-pager || true
