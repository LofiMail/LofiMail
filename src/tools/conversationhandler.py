
class ConversationNode:
    def __init__(self, uid, msg_id, metadata=None):
        self.uid = uid
        self.msg_id = msg_id #Careful, could be malformed.
        self.metadata = metadata or {}
        self.children = []
        self.parent = None  # Optional


