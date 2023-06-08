import datetime
import jsonlines

# Appends json to a jsonl file
def append_to_jsonl(timeline, file_path):
	print("Writing contents to jsonl...")

	# Sort major events array by timestamp
	sorted_timeline = sorted(timeline, key=lambda event: int(event['date']))

	# Pretty print JSON of human datetime
	for event in sorted_timeline:
		date = datetime.datetime.fromtimestamp(int(event['date'])/1000).strftime('%c')
		event['date_pretty'] = date
		# print(f"[{date}] {event['name']} ({len(event['citationIds'])})")

	with jsonlines.open(file_path, mode='a') as writer:
		for item in sorted_timeline:
			writer.write(item)