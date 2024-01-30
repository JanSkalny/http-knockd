# http-knockd
dockerized http "port" knocker using netfilter ipset command

## Installation
1. clone repo
2. install docker, docker-compose, ipset and redis-cli
3. create .env based on env.example
4. run `docker-compose up -d` to get portal running
5. run `knockd.sh` on host (via supervisor / systemd / etc.)
6. use KNOCK ipset list inside iptables ACCEPT rules...
7. create user list under in `db/users.json`

### Manually
```
# get code and configure app
git clone https://github.com/JanSkalny/http-knockd.git /opt/http-knockd
cd /opt/http-knockd
cat example.env | sed 's/example.com/foo.bar/'

# install host dependencies
apt-get install docker-compose docker-ce ipset redis-tools supervisor

# run main portal
docker-compose up -d

# set-up supervisor to run ipset glue (knockd.sh)
cat << 'EOF' > /etc/supervisor/conf.d/knockd.conf
[program:knockd]
command=/opt/http-knockd/knockd.sh
user=root
autostart=true
autorestart=true
startsecs=10
startretries=1000000
redirect_stderr=true
stdout_logfile=/var/log/knockd.log
EOF
supervisorctl reload

# add following to your firewall script (example usage)
ipset create KNOCK hash:ip timeout 1800 || true
iptables -I INPUT 4 -p udp -m set --match-set KNOCK src --dport 10001 -j ACCEPT
```

### Via ansible role
see JanSkalny/ansible-roles-common/http-knockd

## Add users
1. generate random pass and hash it using sha256
```
pw=$(openssl rand -base64 16 | tr -d '+-/='); echo "pw: $pw"; echo -n $pw | sha256sum
```
2. add user to `db/users.json` file (dict)
3. validate via `jq . db/users.json`

restart of app container is NOT needed

## Nicer login form
1. chatgpt:
```
be brief, single html file, code only.
login form with css. post username and password to /
jinja success or error variables.
on success, display "Users from {{ success }} can initiate connections..." message and after {{ timeout }} seconds return to login dialog.
on error, display {{ error }} message.
```
2. modify templates/form.html
3. re-build app image
```
docker-compose down
docker-compose build app
docker-compose up -d
```

## Troubleshooting
```
supervisorctl status
docker ps
ipset list
jq . /opt/http-knockd/db/users.json
docker-compose logs -f
tail -f /var/log/knockd.log
```
