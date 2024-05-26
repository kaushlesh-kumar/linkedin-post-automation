from core.linkedin import LinkedIn
#from core.azuregpt import AzureGpt
from core.ollama_model import OllamaMistral
from core.scraper import Scraper
from core.github_scaper import Scraper_git
import arxivscraper
from pypdf import PdfReader
import wget
import os
import nltk
nltk.download('punkt')
from nltk.tokenize import word_tokenize
import random
from re import sub

from utils import get_file_data, custom_print

#get todays date
from datetime import date, timedelta

def count_tokens(text):
    tokens = word_tokenize(text)
    return len(tokens)

def break_up_file(tokens, chunk_size, overlap_size):
    if len(tokens) <= chunk_size:
        yield tokens
    else:
        chunk = tokens[:chunk_size]
        yield chunk
        yield from break_up_file(tokens[chunk_size-overlap_size:], chunk_size, overlap_size)

def break_up_file_to_chunks(text, chunk_size=1000, overlap_size=50):
    #print(text)
    tokens = word_tokenize(text)
    return list(break_up_file(tokens, chunk_size, overlap_size))

def convert_to_detokenized_text(tokenized_text):
    prompt_text = " ".join(tokenized_text)
    prompt_text = prompt_text.replace(" 's", "'s")
    return prompt_text

class ContentManager:
    @staticmethod
    def load_config(fpath):
        return get_file_data(fpath)

    def __init__(self, config_path):

        self.config = self.load_config(config_path)

        # Initialize all config options as instance variables
        self.cookies            = self.config.get("cookies")
        # self.chatgpt            = AzureGpt(self.config.get("open_ai_api_key"))
        self.ollama1             = OllamaMistral(self.config.get("open_ai_api_key"))
        self.urls               = self.config.get("websites")
        self.preamble           = self.config.get("gpt_preamble")
        self.bio                = self.config.get("bio")
        self.gpt_token_limit    = self.config.get("gpt_token_limit")
        self.scrape_char_limit  = self.config.get("scrape_char_limit")

    def fetch_website_content(self):
        # TODO: look into using chatgpt to format scraped data.
        content = []
        for url in [random.choice(self.urls)]:
            print(url)
            if url == "https://arxiv.org/":
                #get todays latest paper from the AI section of arxive and scrape the HTML version of full paper
                today = date.today()
                print(today, type(today))
                scraper = arxivscraper.Scraper(category='cs', date_from=str(today - timedelta(2)), date_until=str(today))
                output = scraper.scrape()
                print("output: ", output)
                
                # in an xml, find the index of all the entities where the created date is between today and two days before
                index = [i for i in range(len(output)) if output[i]['created'] > str(today - timedelta(4)) and output[i]['created'] < str(today)]
                search_keywords = ["artificial intelligence", "neural network", "deep learning", "machine learning","cyber security", "mlops", "privacy"]
                #from the list of indexes, find the indexes where the abstract contains one of the search_keywords
                index = [i for i in index if any(word in output[i]['abstract'].lower() for word in search_keywords)]
                print("index: ", index)
                # select a random index from the list of indexes
                random_index = random.choice(index)
                #print the url at the random index
                print(output[random_index]['url'])
                # replace abs in the url with pdf
                selected_url = output[random_index]['url'].replace("abs", "pdf")+ ".pdf"
                
                #download the pdf
                wget.download(selected_url, 'paper.pdf',) 
                #convert the pdf to text
                content =''
                pdf = PdfReader("paper.pdf")
                num_pages = len(pdf.pages)
                for i in range(num_pages):
                    page=pdf.pages[i]
                    content = content + ' ' +page.extract_text()
                token_count = count_tokens(content)
                print(f"Number of tokens: {token_count}")
                #delete the pdf
                os.remove("paper.pdf")
            
            else:
                if url == "https://github.com/":
                    # get the urls of trending repos from github
                    print("github")
                    url = 'https://github.com/trending/'
                    scraped, selected_url = Scraper_git(url, self.scrape_char_limit).fetch_content()
                    content = scraped
                    
                                
        return content, selected_url

    def process_gpt_response(self, content):
        collated_response = []
        chunks = break_up_file_to_chunks(content)
        for i, chunk in enumerate(chunks):
            print(f"Chunk {i}: {len(chunk)} tokens")
        
        gpt_res = ''
        for i, chunk in enumerate(chunks):
            # Combine preamble, bio, and website content into the correctly formatted messages
            print('Pass:',i+1)
            print('chunk:',chunks[i])
            gpt_messages = [
                {"role": "system", "content": self.preamble},
                {"role": "system", "content": self.bio},
            ] + [
                {"role": "user", "content": gpt_res + convert_to_detokenized_text(chunks[i])}
            ]
            print(gpt_messages)
            print('total tokens:', count_tokens(' '.join([str(elem) for elem in gpt_messages])))
            #gpt_res = self.chatgpt.ask(gpt_messages, self.gpt_token_limit)
            gpt_res = self.ollama1.ask(gpt_messages, self.gpt_token_limit)

            # collated_response.append(gpt_res)

        # prompt_request = [
        #         {"role": "system", "content": self.preamble},
        #         {"role": "system", "content": self.bio},
        #         {"role": "system", "content": 'Consolidate these summaries:'}
        #     ] + [
        #         {"role": "user", "content": item} for item in collated_response
        #     ]

        # gpt_res1 = self.chatgpt.ask(prompt_request, self.gpt_token_limit)
        
        if not gpt_res:
            return None

        return str(gpt_res)

    def post_content(self):
        content = None
        while content is None:
            content, selected_url         = self.fetch_website_content()

        gpt_response    = self.process_gpt_response(content)
        if not gpt_response:
            custom_print("Error: gpt response empty")
            return

        custom_print("Post: " + sub(r'\n+', ' ', gpt_response))

        linkedin        = LinkedIn(self.cookies)

        # #linkedin.post_file(gpt_response, selected_url, ["media", "burndown.png"])
        linkedin.post(gpt_response, selected_url)
