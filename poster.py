import configparser
import os
from mastodon import Mastodon
from cryptography.fernet import Fernet

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
credentials = os.path.join(ROOT_DIR, 'credentials', 'config.ini')
credentials_folder = os.path.join(ROOT_DIR, 'credentials')
key_file = os.path.join(ROOT_DIR, 'credentials', 'key.key')
encrypted_credentials = os.path.join(ROOT_DIR, 'credentials', 'config.ini.encrypted')

if os.path.exists(credentials):
    os.remove(credentials)

if not os.path.exists(credentials_folder):
    os.makedirs(credentials_folder)

if os.path.exists(key_file):
    with open(key_file, 'rb') as f:
        key = f.read()
else:
    key = Fernet.generate_key()
    with open(key_file, 'wb') as f:
        f.write(key)

if not os.path.exists(encrypted_credentials):
    url = input("Enter the full URL (e.g., https://mastodon.social) of your Mastodon instance:\n")
    email = input("Enter your email address:\n")
    password = input("Enter your password:\n")

    app_info = Mastodon.create_app("Terminal", api_base_url=url)
    client_id, client_secret = app_info

    mastodon = Mastodon(client_id=client_id, client_secret=client_secret, api_base_url=url)
    access_token = mastodon.log_in(email, password)

    config = configparser.ConfigParser()
    config['MASTODON'] = {'url': url,
                          'email': email,
                          'password': password,
                          'client_id': client_id,
                          'client_secret': client_secret,
                          'access_token': access_token}

    with open(credentials, 'w') as configfile:
        config.write(configfile)

    with open(credentials, 'rb') as f:
        data = f.read()

    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(data)

    with open(encrypted_credentials, 'wb') as f:
        f.write(encrypted_data)

    os.remove(credentials)

config = configparser.ConfigParser()
with open(encrypted_credentials, 'rb') as f:
    encrypted_data = f.read()
fernet = Fernet(key)
data = fernet.decrypt(encrypted_data)

with open(credentials, 'wb') as f:
    f.write(data)

config.read(credentials)
url = config['MASTODON']['url']
email = config['MASTODON']['email']
password = config['MASTODON']['password']
client_id_str = config['MASTODON']['client_id']
client_secret_str = config['MASTODON']['client_secret']
access_token_str = config['MASTODON']['access_token']

mastodon = Mastodon(client_id=client_id_str, client_secret=client_secret_str, access_token=access_token_str, api_base_url=url)

app_active = True

while app_active:
    if os.path.exists(credentials):
        os.remove(credentials)

    post_text = input("What do you want to say?:\n")
    media_active = True
    media_ids = []
    sensitive = False
    
    while media_active:
        media_question = input("Do you want media? (Y/N)\n")
        
        if media_question not in ("Y", "N"):
            print("Invalid input, 'Y' or 'N' are only allowed.")
            continue
        
        if media_question == "Y":
            filename = input("Enter the path to the media file:\n")
            try:
                media_dict = mastodon.media_post(filename)
                media_ids = [media_dict['id']]
            except Exception as media_except:
                print(f"Error trying to upload media: {media_except}")
                continue
            
            while True:
                spoiler_media = input("Do you want to add a spoiler to the media? (Y/N)\n")
                
                if spoiler_media not in ("Y", "N"):
                    print("Invalid input, 'Y' or 'N' are only allowed.")
                    continue
                
                sensitive = spoiler_media == "Y"
                break
            
            media_active = False
        
        elif media_question == "N":
            media_active = False
    
    content_warning = input("Do you want to add a content warning? (Y/N)\n")

    if content_warning == "Y":
        warning_text = input("Enter the content warning text:\n")
    else:
        warning_text = None

    try:
        mastodon.status_post(status=post_text, media_ids=media_ids, sensitive=sensitive, spoiler_text=warning_text)
        print("Post successful!")
    except Exception as post_except:
        print(f"Error trying to post: {post_except}")

    continue_app = input("Do you want to make another post? (Y/N)\n")
    
    while True:
        if continue_app not in ("Y", "N"):
            print("Invalid input, 'Y' or 'N' are only allowed.")
            continue
        if continue_app == "N":
            quit()
        if continue_app == "Y":
            break