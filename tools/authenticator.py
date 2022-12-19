import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader


with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

passwords = [str(data['password']) for data in config['credentials']['usernames'].values()]
print(passwords)

hashed_passwords = stauth.Hasher(passwords).generate()

for data, hash in zip(config['credentials']['usernames'].values(), hashed_passwords):
    print(data['password'], '--->', hash)
    data['password'] = hash

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)