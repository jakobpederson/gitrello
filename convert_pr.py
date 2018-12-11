from argparse import ArgumentParser

from gitrello import Gitrello
import github
import trello
import settings


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('--pr_id', required=True)
    parser.add_argument('--repo', required=True)
    args = parser.parse_args()

    g = github.Github(settings.GITHUB_TOKEN).get_user()
    client = trello.TrelloClient(api_key=settings.API_KEY, token=settings.API_TOKEN)
    board = client.get_board(settings.BOARD_ID)
    repo = [x for x in g.get_repos() if x.name == args.repo][0]
    pull = repo.get_pull(int(args.pr_id))
    gitrello = Gitrello(pull, board)
    card = gitrello.create_card()
