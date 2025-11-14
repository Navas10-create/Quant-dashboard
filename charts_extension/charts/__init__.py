from flask_socketio import SocketIO

# Create and export a global SocketIO instance
socketio = SocketIO(cors_allowed_origins="*")
