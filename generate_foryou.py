import datetime
import requests
import json
import sys
import csv
import tiktoken

from helpers.enhance import enhance_company

# Token
DIFFBOT_TOKEN = "" # Your Diffbot Token (get one at app.diffbot.com/get-started)
OPENAI_AUTH = "" # Your OpenAI Bearer Token (get one at platform.openai.com)

# Grab arguments
company_name = sys.argv[1]

# Enhance the Company Input
company_data = enhance_company(DIFFBOT_TOKEN, company_name)

# Query for Headlines from Diffbot Knowledge Graph
dql = f"type:Article title:\'{company_data['name']}\' categories.name:\'Business\' tags.uri:\'https://app.diffbot.com/entity/{company_data['id']}\'  language:\'en\' date<=30d sortBy:date"
res = requests.get(f'https://kg.diffbot.com/kg/v3/dql?token={DIFFBOT_TOKEN}&query={dql}&size=60&from=0&cluster=best&format=csv&exportspec=title;id;date.timestamp')
print(dql)
if res.status_code == 200:
	headlines_res = res.text
	if len(res.text) == 0:
		raise Exception("No articles found.")
else:
	print(f"Error querying for articles")

# Build Prompt for ChatGPT
prompt = f"The following is the CSV output of a search for articles on the company {company_data['name']}:"
prompt += f"\n\n ```\n"
prompt += headlines_res
prompt += f"```\n\n"
prompt += f"Based on the above headlines, summarize any major events that happened at {company_data['name']} in an array of JSONs with each JSON item having a key name, date (in its original epoch time date format), and an array of citationIds to the relevant articles. Cluster similar headlines to the same event, even if they may not occur on the same date. If they do not have the same date, use the earliest known date."

# Edit this line to the signals you want in your FYP
prompt += f"Only summarize headlines directly related to politics. If there are no headlines related to politics, return an empty array. Summaries should include a verb. Only return the JSON, no further text or explanation, do not use markdown."

# Count Tokens for GPT Request
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
		print(gpt_answer) # Pretty printed by default
	except Exception as e:
		print(e)
		print(gpt_answer)
else:
	gpt_res = res.json()
	print(gpt_res.get('error'))