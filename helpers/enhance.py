import requests

def enhance_company(DIFFBOT_TOKEN, company_name):
	res = requests.get(f'https://kg.diffbot.com/kg/v3/enhance?token={DIFFBOT_TOKEN}&type=Organization&name={company_name}&filter=id%20name%20foundingDate%20founders%20investments')
	if res.status_code == 200:
		company_res = res.json()
		company_data = company_res['data'][0]['entity']
		if not company_data.get('id') or not company_data.get('name') or not company_data.get('foundingDate'):
			raise Exception("Company is a stub entity. Key details missing.")
		print(f"{company_name} ({company_data['id']}), founded on {company_data['foundingDate']['str']}, Enhanced. ")
		return company_data
	else:
		raise Exception("Company Not Found")