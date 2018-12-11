from unittest import TestCase
import mock
import github
import settings
import trello
import logging
import logging.config
import gitrello

logging.disable(logging.CRITICAL)


class GitrelloTests(TestCase):

    def setUp(self):
        g = github.Github(settings.GITHUB_TOKEN)
        self.user = g.get_user()
        self.org = [x for x in self.user.get_orgs() if x.login == 'this-is-a-test-org'][0]
        self.repo_dict = {x.name: x for x in self.org.get_repos()}
        self.repo = self.repo_dict['this_is_also_a_test']
        self.client = trello.TrelloClient(api_key=settings.API_KEY, token=settings.API_TOKEN)
        self.board = self.client.get_board('PnJ7VVo8')
        self.clear_board()
        self.pull = self.repo.get_pulls('open')[0]
        self.gitrello = gitrello.Gitrello(self.pull, self.board)
        self.commits = self.pull.get_commits()
        self.card = self.gitrello.create_card()

    def clear_board(self):
        for trello_list in self.board.open_lists():
            if trello_list.name != 'open prs':
                trello_list.close()
        for card in self.board.open_cards():
            card.delete()
        for label in self.board.get_labels():
            if label.name:
                self.delete_label(label)

    def delete_label(self, label):
        self.client.fetch_json('/labels/{0}'.format(label.id), http_method='DELETE', post_args={'id': label.id})

    def test_get_card_url_can_parse_out_url_from_string(self):
        url = self.gitrello.get_card_url('xhd;fdaslkdfhadlkfhaldkfhaskjdfha[https://trello.com/c/tpRwlepo/16-junks]')
        self.assertEqual('https://trello.com/c/tpRwlepo/16-junks', url)

    def test_get_commits_returns_list_of_urls_of_commits(self):
        result = self.gitrello.get_commits()
        expected = [
            'https://trello.com/c/cHZouqvS/5-wick',
            'https://trello.com/c/3ZTj2oNL/6-wick',
            'https://trello.com/c/bXYeXP5K/8-wick',
            'https://trello.com/c/czwnN8xf/9-wick',
            'https://trello.com/c/uAKgHi8B/10-wick',
            'https://trello.com/c/XpBgjYV9/11-wick',
            'https://trello.com/c/klm0SqkW/12-wick',
            'https://trello.com/c/4MQeYYVA/13-wick',
            'https://trello.com/c/FPp7PFAf/14-wick',
            'https://trello.com/c/tpRwlepo/16-junks',
            'https://www.what.com/x/y/z/',
            'https://trello.com/c/DHcskmJi/119-test',
        ]
        self.assertCountEqual(expected, result)

    def test_card_is_created_with_correct_name_attachment_and_label(self):
        name = self.card.name
        self.assertEqual('Pull Request 1', name)
        expected_urls = [
            'https://trello.com/c/cHZouqvS/5-wick',
            'https://trello.com/c/3ZTj2oNL/6-wick',
            'https://trello.com/c/bXYeXP5K/8-wick',
            'https://trello.com/c/czwnN8xf/9-wick',
            'https://trello.com/c/uAKgHi8B/10-wick',
            'https://trello.com/c/XpBgjYV9/11-wick',
            'https://trello.com/c/klm0SqkW/12-wick',
            'https://trello.com/c/4MQeYYVA/13-wick',
            'https://trello.com/c/FPp7PFAf/14-wick',
            'https://trello.com/c/tpRwlepo/16-junks',
            'https://www.what.com/x/y/z/',
            'https://trello.com/c/DHcskmJi/119-test',
        ]
        result_urls = [x['name'] for x in self.card.checklists[0].items]
        self.assertCountEqual(expected_urls, result_urls)
        expected_labels = ['this_is_also_a_test']
        self.assertCountEqual(expected_labels, [x.name for x in self.card.labels])
        result_attachment = self.card.attachments[0]
        expected_url = 'https://github.com/this-is-a-test-org/this_is_also_a_test/pull/1'
        self.assertEqual(expected_url, result_attachment['url'])

    def test_uses_label_that_already_exists_instead_of_duplicating(self):
        expected = self.board.get_labels()[0]
        label = self.gitrello.get_or_create_label()
        self.assertEqual(expected.name, label.name)
        self.assertEqual(expected.color, label.color)


class ChecklistTests(TestCase):

    @mock.patch('gitrello.Gitrello.name')
    def setUp(self, name):
        name.return_value = 'test'
        g = github.Github(settings.GITHUB_TOKEN)
        self.user = g.get_user()
        self.org = [x for x in self.user.get_orgs() if x.login == 'this-is-a-test-org'][0]
        self.repo_dict = {x.name: x for x in self.org.get_repos()}
        self.repo = self.repo_dict['this_is_also_a_test']
        self.client = trello.TrelloClient(api_key=settings.API_KEY, token=settings.API_TOKEN)
        self.board = self.client.get_board('PnJ7VVo8')
        self.pull = self.repo.get_pulls('open')[0]
        self.gitrello = gitrello.Gitrello(self.pull, self.board)
        self.commits = self.pull.get_commits()
        for card in self.board.open_cards():
            card.delete()
        self.trello_list = [x for x in self.board.open_lists()][0]
        test_card = self.trello_list.add_card('test')
        test_card.add_checklist('test checklist', ['a', 'b', 'c'], itemstates=[True, False, False])
        test_card.fetch()
        self.card = self.gitrello.create_card()

    def test_adds_check_list_items_to_preexisting_checklist_and_keeps_original_items(self):
        result = [x['name'] for x in self.card.checklists[0].items]
        expected = [
            'a',
            'b',
            'c',
            'https://trello.com/c/4MQeYYVA/13-wick',
            'https://trello.com/c/3ZTj2oNL/6-wick',
            'https://trello.com/c/uAKgHi8B/10-wick',
            'https://trello.com/c/cHZouqvS/5-wick',
            'https://trello.com/c/czwnN8xf/9-wick',
            'https://trello.com/c/XpBgjYV9/11-wick',
            'https://trello.com/c/bXYeXP5K/8-wick',
            'https://www.what.com/x/y/z/',
            'https://trello.com/c/DHcskmJi/119-test',
            'https://trello.com/c/klm0SqkW/12-wick',
            'https://trello.com/c/tpRwlepo/16-junks',
            'https://trello.com/c/FPp7PFAf/14-wick'
        ]
        self.assertCountEqual(expected, result)

    def test_maintains_checked_state_of_prexisting_checklist_item(self):
        result = {x['name']: x['checked'] for x in self.card.checklists[0].items}
        expected = {
            'a': True,
            'b': False,
            'c': False,
            'https://trello.com/c/tpRwlepo/16-junks': False,
            'https://trello.com/c/FPp7PFAf/14-wick': False,
            'https://trello.com/c/3ZTj2oNL/6-wick': False,
            'https://trello.com/c/uAKgHi8B/10-wick': False,
            'https://trello.com/c/klm0SqkW/12-wick': False,
            'https://trello.com/c/DHcskmJi/119-test': False,
            'https://trello.com/c/bXYeXP5K/8-wick': False,
            'https://trello.com/c/czwnN8xf/9-wick': False,
            'https://trello.com/c/4MQeYYVA/13-wick': False,
            'https://trello.com/c/XpBgjYV9/11-wick': False,
            'https://trello.com/c/cHZouqvS/5-wick': False,
            'https://www.what.com/x/y/z/': False
        }
        self.assertCountEqual(expected, result)
