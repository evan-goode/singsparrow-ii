default: all

all:
	./setup.py build

install:
	./setup.py install
	install -m 644 singsparrow-ii.service /etc/systemd/system/
	[ -f /etc/singsparrow-ii.toml ] || install -m 644 singsparrow-ii.toml /etc/singsparrow-ii.toml
	systemctl daemon-reload || true
	systemctl status singsparrow-ii.service --no-pager || true
