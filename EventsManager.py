class EventsManager:
    def __init__(self):
        self.gui_client = None

    def set_gui_client(self, gui_client):
        self.gui_client = gui_client

    def update(self, event, text):
        if self.gui_client is not None:
            self.gui_client.notify(event, text)
