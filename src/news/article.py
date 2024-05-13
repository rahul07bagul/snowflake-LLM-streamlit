import logging
import requests
from bs4 import BeautifulSoup
from news.story import Story
from news.comment import Comment
from newsplease import NewsPlease
from datetime import datetime, timedelta

def request_hn_id_details(hn_id):
	return requests.get(f'https://hacker-news.firebaseio.com/v0/item/{hn_id}.json').json()

def request_hn_best_stories():
	logging.debug('request_hn_best_stories')
	return requests.get(f'https://hacker-news.firebaseio.com/v0/topstories.json?print=pretty').json()

def get_comment(comment_id):
	logging.debug(f'Getting comment for comment_id {comment_id}')
	full_comment = request_hn_id_details(comment_id)
	if ('text' not in full_comment):
		return None
	soup = BeautifulSoup(full_comment['text'], 'html.parser')
	comment_text = soup.text
	return Comment(id=comment_id, text=comment_text)

def get_comments(comment_ids, number_of_comments):
	for comment_id in comment_ids:
		if (number_of_comments <= 0):
			break
		comment = get_comment(comment_id)
		if (comment is not None):
			number_of_comments -= 1
			yield comment

def top_comments(hn_story_id, number_of_comments=3):
	logging.info(f'Getting comments for story {hn_story_id}')
	hn_story = request_hn_id_details(hn_story_id)
	if ('kids' in hn_story):
		return [comment for comment in get_comments(hn_story['kids'], number_of_comments)]
	return []

def best_story_ids():
	logging.info(f'Fetching best stories from API')
	return request_hn_best_stories()

def get_story(story_id):
	logging.info(f'Getting story {story_id}')
	hn_story = request_hn_id_details(story_id)
	hn_link = f'https://news.ycombinator.com/item?id={story_id}'
	story_link = hn_story['url'] if 'url' in hn_story else hn_link
	return Story(
		id=story_id,
		title=hn_story['title'],
		link=story_link,
		hn_link=hn_link,
		score=hn_story['score'],
		by=hn_story['by'],
		posted_time=hn_story['time'],
		top_comments=top_comments(story_id))

def get_articles():
    logging.debug('get_articles')
    print("Getting latest articles....")
    articles = []
    story_ids = best_story_ids()
    # Process only the first 10 story IDs
    for story_id in story_ids[:10]:
        story = get_story(story_id)  # Get story details
        try:
            article = NewsPlease.from_url(story.link)  # Fetch article using its link
            article.id = story_id
            article.hn_link = story.hn_link
            article.score = story.score
            article.by = story.by
            article.posted_time = story.posted_time
            articles.append(article)
        except Exception as e:
            print(f"Failed to fetch article for story {story_id}: {e}")

    return articles
