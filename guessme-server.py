import random
import socket
import selectors
import types

HOST = "127.0.0.1"
PORT = 65432

class Game:
    def __init__(self):
        self.max_guess = 10
        self.guesses_left = self.max_guess
        self.answer = random.randint(1, 100)
        self.state ="running"

    def handle_guess(self, guess):
        if self.state != "running":
            return "The game has ended.Start new game.OK?"

        self.guesses_left -= 1
        if guess == self.answer:
            self.state = "Just Lucky"
            return "Correct! You win!\n"
        elif guess < self.answer:
            if self.guesses_left == 0:
                self.state = "HAHA Try Again"
            return "Too low.\n"
        else:
            if self.guesses_left == 0:
                self.state = "HAHA Try Again"
            return "Too high.\n"

sel = selectors.DefaultSelector()

lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((HOST, PORT))
lsock.listen()
print(f"Listening on {(HOST, PORT)}")
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

socks = []

def accept_wrapper(sock):
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    game = Game()
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", game=game)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)
    socks.append(conn)

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    game = data.game
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)
        if recv_data:
            guess = int(recv_data.decode())
            send_data = game.handle_guess(guess).encode()
            sock.sendall(send_data)
            if guess == game.answer or game.guesses_left == 0:
                print(f"Closing connection to {data.addr}")
                sel.unregister(sock)
                sock.close()
                socks.remove(sock)
        else:
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
            socks.remove(sock)

try:
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                 accept_wrapper(key.fileobj)
            else:
                service_connection(key, mask)
except KeyboardInterrupt:
    print("Caught keyboard interrupt, exiting")
finally:
    sel.close()