from flask import Flask, request, render_template, abort
from datetime import datetime
from sys import stderr
from html import escape
import json, hashlib, os, redis, ipaddress


# write debug messages to stderr
def debug(*messages):
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), *messages, file=stderr)


app = Flask(__name__)

# Connect to redis
redis_host = os.environ.get("REDIS_HOST", "localhost")
redis_client = redis.Redis(host=redis_host, port=6379, db=0)

# validate rate limit parameters
RATE_LIMIT_MAX_REQUESTS = int(os.environ.get("RATE_LIMIT_REQUESTS", "3"))
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", "60"))
if RATE_LIMIT_MAX_REQUESTS <= 0:
    RATE_LIMIT_MAX_REQUESTS = 3
if RATE_LIMIT_WINDOW <= 0:
    RATE_LIMIT_WINDOW = 60

# knockd timeout (for ui pruposes)
TIMEOUT = int(os.environ.get("TIMEOUT", "1800"))
if TIMEOUT <= 0:
    TIMEOUT = 1800

# Define a dictionary to store the request counts for each IP address
request_counts = {}


@app.route("/", methods=["GET", "POST"])
def login():
    # Get the IP address of the requester
    ip_address = request.headers.get("X-Forwarded-For")
    try:
        ipaddress.ip_address(ip_address)
    except ValueError:
        abort(503, "Invalid client IP address")

    # Increment the count for the IP and set the key to expire in N seconds
    key = f"rate_limit:{ip_address}"
    count = redis_client.incr(key)
    if count == 1:
        redis_client.expire(key, RATE_LIMIT_WINDOW)

    # Check if the IP address has exceeded the rate limit
    if count > RATE_LIMIT_MAX_REQUESTS:
        debug(f"ratelimit addr={ip_address}")
        abort(
            429,
            f"You have exceeded the rate limit of {RATE_LIMIT_MAX_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds",
        )

    # Load users data
    with open("db/users.json", "r") as file:
        users = json.load(file)

    error = ""
    success = ""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Hash the password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Verify username and password
        if username in users and users[username] == hashed_password:
            debug(f"auth-success user={username} addr={ip_address}")
            success = escape(ip_address)
            add_ip_to_ipset(ip_address)
        else:
            debug(f"auth-fail user={username} addr={ip_address}")
            error = "Login failed!"

    return render_template("form.html", success=success, error=error, timeout=TIMEOUT)


def add_ip_to_ipset(ip_address):
    redis_client.publish("knockd", ip_address)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
