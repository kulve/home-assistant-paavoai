class AbstractConversationAgent:
    pass

class ConversationInput:
    def __init__(self, text, language="fi", conversation_id="test"):
        self.text = text
        self.language = language
        self.conversation_id = conversation_id

class ConversationResult:
    def __init__(self, response, conversation_id=None):
        self.response = response
        self.conversation_id = conversation_id

class IntentResponse:
    def __init__(self, speech=None, language=None):
        self.speech = {"plain": {"speech": speech}}
        self.language = language

    def async_set_speech(self, speech):
        self.speech = {"plain": {"speech": speech}}

class HomeAssistant:
    pass