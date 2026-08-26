# Socket handlers are registered in app.sockets.chat_socket.
# This file intentionally does NOT register any handlers to avoid
# duplicate event registration (see chat_socket.py for the single
# authoritative implementation of join_conversation and send_message).
