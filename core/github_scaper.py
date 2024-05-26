import requests
from bs4 import BeautifulSoup
import re
import random
from core.scraper import Scraper  
  
def get_random_key(dictionary):  
    return random.choice(list(dictionary.keys())) 

class Scraper_git:
    def __init__(self, url, character_limit=5000):
        self.url = url
        self.character_limit = character_limit

    def fetch_content(self):
        response = requests.get(self.url)
        if response.status_code == 200:
            print(response.text)
            return self.parse(response.text)
        return None

    def parse(self, content):
          
        soup = BeautifulSoup(content, 'html.parser')  
        repos_dict = {}
        repos = soup.find_all('article', class_='Box-row')  
        
        for repo in repos:  
            # Get repository name and link  
            repo_name_tag = repo.find('h2', class_='h3').find('a')  
            repo_name = repo_name_tag.text.strip()  
            repo_link = 'https://github.com' + repo_name_tag['href']  
        
            # Get description  
            description_tag = repo.find('p', class_='col-9')  
            description = description_tag.text.strip() if description_tag else "No description"  
        
            # Get programming language  
            language_tag = repo.find('span', itemprop='programmingLanguage')  
            language = language_tag.text.strip() if language_tag else "No specific language"  

            # Store details in dictionary  
            repos_dict[repo_name] = {  
                'link': repo_link,  
                'description': description,  
                'language': language  
            }
        
        for name, details in repos_dict.items():  
            print(f'Repo Name: {name}')  
            print(f'Details: {details}')  
            print('-----------------------------')

        language_list = ['python', 'jupyter notebook','java']
        keyword_list = ['machine learning', 'deep learning', 'data science', 'neural network', 'cyber security', 'mlops', 'privacy', 'vision', 'nlp', 'artificial intelligence', 'ai', 'data analysis', 'data analytics', 'visualization', 'data science', 'LLM']
        selected = {}
        for name, details in repos_dict.items():
            if any(word in details['description'].lower() for word in keyword_list) and any(word in details['language'].lower() for word in language_list):
                print('selected')
                print(f'Repo Name: {name}')  
                print(f'Details: {details}')  
                print('-----------------------------')
                # store the repo name and link in a dictionary
                selected[name] = details
         
                # write a function to first randomly select a repo from the selected dictionary
                random_key = get_random_key(selected)

                
                selected_url = selected[random_key]['link']
                # replace github.com with raw.githubusercontent.com
                raw_selected_url = selected_url.replace("github.com", "raw.githubusercontent.com")
                raw_readme_url = raw_selected_url + '/main/README.md'

                # Scarp the readme file for content
                scraped = Scraper(raw_readme_url, self.character_limit).fetch_content()


        return scraped, selected_url
