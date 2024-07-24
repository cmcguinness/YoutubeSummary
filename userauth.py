#    ┌─────────────────────────────────────────────────────────┐
#    │                   User Authentication                   │
#    │                                                         │
#    │              Yes, it's cheesy as all hell.              │
#    └─────────────────────────────────────────────────────────┘
import os
import json

# We have our default user of admin, admin, but if you specify an environment
# variable USERDB with a value like { "bob": "pass1", "tom": "pass2" }, then it
# will use that instead.
user_list = {
    "admin": "admin",
}


def authenticate(user,password):
    global user_list
    env_users = os.getenv('USERDB')
    users = user_list
    if env_users is not None:
        users = json.loads(env_users)
    return user in users and users[user] == password
