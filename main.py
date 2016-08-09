from slackclient import SlackClient
from recast import Recast
from json import loads
import time
import pickle
import feedparser

class Rss:
    def __init__(self, link):
        self.link = link
        parse = feedparser.parse(self.link)
        try:
            a = parse["version"]
            self.title = parse.feed.title
            self.subtitle = parse.feed.subtitle
            self.printLink = parse.feed.link
            self.error = None
        except KeyError:
            self.error = parse["bozo_exception"]

    def __str__(self):
        return self.title + " - " + self.subtitle

    def getLatest(self, number):
        try:
            parse = feedparser.parse(self.link)
            response = self.title + ":\n>"
            for entry in parse["entries"][:number]:
                response += entry.title + ": " + entry.link + "\n>"
            return response
        except KeyError:
            return "Error while loading " + self.title + ": " + parse["bozo_exception"]

class Logic:
    def __init__(self):
        try:
            with open("settings", "rb") as f:
                self.settings = pickle.load(f)
        except IOError:
            self.settings = {
                    "rss" : [],
                    "update-size" : 2,
                    }
        self.intents = {
                "greetings" : self.greetings,
                "help" : self.help,
                "list_rss" : self.list,
                "add_rss" : self.add,
                "thanks" : self.thanks,
                "size" : self.size,
                "news" : self.news,
                }

    def save(self):
        with open("settings", "wb") as f:
            pickle.dump(self.settings, f)

    def greetings(self, sentence):
        return "Hello! Ask me what I can do! :simple_smile:"

    def help(self, sentence):
        return """I can help you with
        `help` - print this help
        `news` - get the latest news from rss
        `list` - list the rss I'm currently monitoring
        `size` - see or set the number of updates I'll display for you"""

    def list(self, sentence):
        if not len(self.settings["rss"]):
            return "I don't monitor anything for now! You should ask me to :simple_smile:"
        response = "Here you are, the rss I'm currently monitoring:\n"
        for rss in self.settings["rss"]:
            response += "- " + str(rss) + "\n"
        return response

    def add(self, sentence):
        try:
            rss = Rss(sentence["entities"]["url"][0]["value"])
            if rss.error is not None:
                return "Sorry I couldn't add the rss you asked for : " + rss.error
            self.settings["rss"].append(rss)
            return "Ok done! I'll monitor this one: " + str(rss)
        except KeyError:
            return "Sorry, can you repeat please?"

    def thanks(self, sentence):
        return "Always here to help :simple_smile:"

    def size(self, sentence):
        try:
            self.settings["update-size"] = sentence["entities"]["number"][0]["value"]
            return "No problem! I'll now display " + str(self.settings["update-size"]) + " entries per rss feed"
        except KeyError:
            return "I'm currently programmed to show " + str(self.settings["update-size"]) + " entries per rss feed"

    def news(self, sentence):
        if not len(self.settings["rss"]):
            return "I'm not monitoring anything yet! You should ask me to do it :simple_smile:"
        response = "Here are the latest news from the feeds:\n"
        for rss in self.settings["rss"]:
            response += rss.getLatest(self.settings["update-size"])
        return response

    def parse(self, intent):
        intent = loads(intent)
        try:
            return self.intents[intent["results"]["intents"][0]](intent["results"]["sentences"][0])
        except (KeyError, IndexError):
            return "Sorry I didn't understand what you meant"

logic = Logic()
recast = Recast("recast.ai key")
slack = SlackClient("slack key")
myChannel = "D1G3XNQSK"
me = "<@U1G436TAM>"
start = time.time()
if slack.rtm_connect():
    try:
        while True:
            msgs = slack.rtm_read()
            for msg in msgs:
                print(msg)
                try:
                    if msg["type"] != "message" or "uploaded a file: " in msg["text"]:
                        continue
                    if float(msg["ts"]) < start:
                        continue
                except KeyError:
                    continue
                channel = msg["channel"]
                text = msg["text"]
                if channel != myChannel and me not in text:
                    continue
                text = text.replace(me, "")
                slack.rtm_send_message(channel, logic.parse(recast.getIntent(text)))
            time.sleep(1)
    except (Exception, KeyboardInterrupt) as e:
        logic.save()
        print(str(e)) 
else:
    print("Error while connecting")
