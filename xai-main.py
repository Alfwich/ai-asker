from xai_sdk import Client
from xai_sdk.chat import user, system

API_KEY = "".join(open('.grok-key', 'r').readlines())


def main():
    client = Client(api_key=API_KEY)

    chat = client.chat.create(model="grok-4")
    chat.append(user("What is the meaning of life, the universe, and everything?"))

    response = chat.sample()
    print(response.content)


if __name__ == "__main__":
    main()
