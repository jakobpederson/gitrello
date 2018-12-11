import github
import random
import re
import settings
import trello


class Gitrello():

    COLORS = [
        'green',
        'yellow',
        'orange',
        'red',
        'purple',
        'blue',
        'sky',
        'lime',
        'pink',
        'black',
    ]

    def __init__(self, pull, board):
        self.client = trello.TrelloClient(api_key=settings.API_KEY, token=settings.API_TOKEN)
        self.pull = pull
        self.board = board
        self.trello_list = [x for x in self.board.open_lists() if x.name == settings.LIST_NAME][0]
        self.label = self.get_or_create_label()
        self.urls = self.get_commits()

    def get_or_create_label(self):
        name = self.pull.url.split('/')[5]
        labels = {x.name: x for x in self.board.get_labels()}
        if name in labels.keys():
            return labels[name]
        color = random.choice(list(self.COLORS))
        return self.board.add_label(name, color)

    def get_card_url(self, text):
        url_check = re.search("(?P<url>https?://[^\s]+)", text)
        if url_check:
            url = url_check.group("url").rstrip(']')
            return url

    def get_commits(self):
        urls = []
        for commit in self.pull.get_commits():
            commit_message_url = [self.get_urls(commit.commit.message)] if self.get_urls(commit.commit.message) else []
            comment_urls = [self.get_urls(x.body) for x in commit.get_comments() if self.get_urls(x.body)]
            urls = urls + comment_urls + commit_message_url
        return self.clean_list(urls)

    def clean_list(self, urls):
        remove_nones = [url for url in urls if url]
        return list(set(remove_nones))

    def get_urls(self, text):
        url = self.get_card_url(text)
        return url if url else None

    def name(self):
        return 'Pull Request {} - {}'.format(self.pull.number, self.label.name)

    def create_card(self):
        name = self.name()
        cards = {card.name: card for card in self.trello_list.list_cards()}
        if name not in cards.keys():
            return self.create_or_update_card(name)
        else:
            card = cards[name]
            card.fetch()
            return self.create_or_update_card(name, card)

    def create_or_update_card(self, name, card=None):
        if card:
            card = self.update_checklists(card)
        else:
            card = self.trello_list.add_card(name)
            card = self.add_checklists(card)
        card.attach(name, url=self.pull.html_url)
        self.add_label(card)
        card.fetch()
        return card

    def add_checklists(self, card):
        card.add_checklist('commits', self.urls)
        return card

    def update_checklists(self, card):
        if card.checklists:
            checklists = card.checklists
            for checklist in checklists:
                items = [x for x in checklist.items]
                self.checklist_update(card, items, checklist)
        return card

    def checklist_update(self, card, items, checklist):
        old_items = [x['name'] for x in items]
        new_items = self.urls
        for item in new_items:
            if item not in old_items:
                checklist.add_checklist_item(item)
        return card

    def add_label(self, card):
        try:
            card.add_label(self.label)
        except trello.exceptions.ResourceUnavailable:
            pass
        return card
