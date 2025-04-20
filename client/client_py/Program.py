from Listener import ClientListener

if __name__ == "__main__":
    listener = ClientListener("http://localhost:5001/receive/")
    listener.start()