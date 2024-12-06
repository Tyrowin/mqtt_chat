import json
import time
from datetime import datetime
from paho.mqtt import client as mqtt_client


class MQTTChat:
    def __init__(self, broker="localhost", port=1883):
        self.broker = broker
        self.port = port
        self.client_id = f"chat-{int(time.time())}"
        self.username = None
        self.current_room = None
        self.connected = False
        self.client = self.setup_client()

    def setup_client(self):
        """Set up MQTT client"""
        # Adjust initialization to avoid ValueError
        client = mqtt_client.Client(self.client_id, protocol=mqtt_client.MQTTv311)

        # Set callback functions
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        return client

    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(self.broker, self.port)
            print(f"Connected to {self.broker}:{self.port}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def on_connect(self, client, userdata, flags, rc):
        """Callback for when connection is established"""
        if rc == 0:
            self.connected = True  # Set connection flag
            print("Connected successfully")
        else:
            print(f"Connection failed with code {rc}")

    def on_message(self, client, userdata, msg):
        """Handle incoming messages"""
        try:
            message = json.loads(msg.payload.decode())
            if (
                message["room"] == self.current_room
                and message["username"] != self.username
            ):
                timestamp = datetime.fromtimestamp(message["timestamp"]).strftime(
                    "%H:%M:%S"
                )
                print(f"\n[{timestamp}] {message['username']}: {message['content']}")
        except json.JSONDecodeError:
            print("Received malformed message")

    def join_room(self, room_name):
        """Join a chat room"""
        if self.current_room:
            self.client.unsubscribe(f"chat/{self.current_room}")

        self.current_room = room_name
        self.client.subscribe(f"chat/{room_name}")
        print(f"Joined room: {room_name}")

        # Announce joining
        self.send_message(f"{self.username} has joined the room")

    def send_message(self, content):
        """Send a message to the current room"""
        if not self.current_room:
            print("Join a room first!")
            return

        message = {
            "username": self.username,
            "room": self.current_room,
            "content": content,
            "timestamp": time.time(),
        }

        self.client.publish(f"chat/{self.current_room}", json.dumps(message))

    def start(self):
        """Start the chat application"""
        # Get username
        self.username = input("Enter your username: ").strip()

        # Connect to broker
        print(f"Connecting to {self.broker}:{self.port}...")
        self.client.loop_start()
        if not self.connect():
            return

        # Wait for connection to complete with a timeout
        timeout = 10  # Maximum wait time in seconds
        start_time = time.time()
        while not self.connected and (time.time() - start_time) < timeout:
            time.sleep(0.1)

        if not self.connected:
            print("Failed to connect to broker. Exiting...")
            return

        print("-----------------------")

        # Prompt for entering room name
        initial_room = input("Enter room name to join: ").strip()
        self.join_room(initial_room)

        # Main chat loop
        try:
            while True:
                message = input("")
                if message.lower() == "/quit":
                    break
                elif message.lower().startswith("/join "):
                    new_room = message[6:].strip()
                    self.join_room(new_room)
                else:
                    self.send_message(message)
        except KeyboardInterrupt:
            pass
        finally:
            self.client.loop_stop()
            self.client.disconnect()
            print("\nDisconnected from chat")


if __name__ == "__main__":
    chat = MQTTChat()
    chat.start()
