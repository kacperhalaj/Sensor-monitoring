from server.server import NetworkServer

if __name__ == "__main__":
    # Utworzenie i uruchomienie serwera sieciowego
    print("Uruchamianie serwera sieciowego...")
    server = NetworkServer()
    server.start()