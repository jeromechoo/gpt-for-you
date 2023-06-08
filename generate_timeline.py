import datetime
import requests
import sys
import json
import jsonlines
import csv
import tiktoken

from helpers.enhance import enhance_company
from helpers.write import append_to_jsonl

# Token
DIFFBOT_TOKEN = "" # Your Diffbot Token (get one at app.diffbot.com/get-started)
OPENAI_AUTH = "" # Your OpenAI Bearer Token (get one at platform.openai.com)

# Grab arguments
company_name = sys.argv[1]

# Enhance the Company Input
company_data = enhance_company(DIFFBOT_TOKEN, company_name)

# Light DQL request to find the number of articles to query for this company
dql = f"type:Article title:\'{company_data['name']}\' categories.name:\'Business\' tags.{{uri:\'https://app.diffbot.com/entity/{company_data['id']}\' score>0.95}} language:\'en\' date.timestamp>={company_data['foundingDate']['timestamp']} revSortBy:date"
res = requests.get(f'https://kg.diffbot.com/kg/v3/dql?token={DIFFBOT_TOKEN}&query={dql}&size=0&from=0')
if res.status_code == 200:
	hits_res = res.json()
	hits = hits_res['hits'] # No. of Articles / 100 is the number of requests to make to DQL + GPT
	print(f"Found {hits} headlines for {company_name}...")
	if hits < 80:
		raise Exception("Not Enough Press Coverage")
else:
	raise Exception("Error Retrieving Articles")

# Loop through requests of DQL, then GPT and append to an array of major events over time
i = 0
increment = 60
while i < hits:
	# DQL for Headlines
	dql = f"type:Article title:\'{company_data['name']}\' categories.name:\'Business\' tags.{{uri:\'https://app.diffbot.com/entity/{company_data['id']}\' score>0.95}} language:\'en\' date.timestamp>={company_data['foundingDate']['timestamp']} revSortBy:date"
	print(f"Querying {i}th iteration...")
	res = requests.get(f'https://kg.diffbot.com/kg/v3/dql?token={DIFFBOT_TOKEN}&query={dql}&size={increment}&from={i}&cluster=best&format=csv&exportspec=title;id;date.timestamp')
	if res.status_code == 200:
		headlines_res = res.text
	else:
		print(f"Error Requesting {i}th Iteration of Headlines")
		continue

	# GPT for Major Events
	prompt = f"The following is the CSV output of a search for articles on the company {company_data['name']}:"
	prompt += f"\n\n ```\n"
	prompt += headlines_res
	prompt += f"```\n\n"
	prompt += f"Based on the above headlines, summarize 1-4 major events that happened at {company_data['name']} in a JSON array of events with each event having a key name, date (in its original epoch time date format), and a JSON array of citationIds to the relevant articles. Cluster similar headlines to the same event, even if they may not occur on the same date. If they do not have the same date, use the earliest known date. Ignore headlines about {company_data['name']}'s stock price, stock performance, dividends, or market performance. Also ignore headlines about gossip, social commentaries, thoughts, potentials, explorations, hearsay, maybes, and opinions. Summaries should include a verb. Only return the JSON, no further text or explanation, do not use markdown."

	# Count Tokens
	encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
	prompt_tokens = len(encoding.encode(prompt))

	res = requests.post("https://api.openai.com/v1/chat/completions", 
		headers={'Content-Type': 'application/json', 'Authorization': OPENAI_AUTH}, 
		json={
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
		"temperature": 0.1, # This ensures the output is as consistent as possible, without being too rigid
		"max_tokens": 4097 - prompt_tokens - 10 # The `messages` JSON around the prompt is about 10 tokens and apparently this counts 🙄
		})
	if res.status_code == 200:
		gpt_res = res.json()
		gpt_answer = gpt_res['choices'][0]['message']['content'].strip()
		# print(gpt_answer)
		try:
			gpt_json = json.loads(gpt_answer)
			# print(gpt_json)
			print(f"Timeline Batch {i} Complete. Top Headline — {gpt_json[0]['name']}")
			append_to_jsonl(gpt_json, f'dist/{company_name}.jsonl')
		except Exception as e:
			print(e)
			print(gpt_answer)
			print(f"{i}th Iteration of GPT Generated Events is a Malformed JSON Object, Stopping...")
			break
	else:
		gpt_res = res.json()
		print(gpt_res.get('error'))
		break
	i += increment