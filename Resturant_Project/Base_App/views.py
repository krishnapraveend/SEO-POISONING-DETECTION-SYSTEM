from django.shortcuts import render,redirect
from django.http import HttpResponse
from Base_App.models import AboutUs, Feedback, ItemList, Items
import requests
from bs4 import BeautifulSoup
import re
import os
import pandas as pd
from .models import Feedback  # Import your Feedback model
from .forms import FeedbackForm  # Import your FeedbackForm

# Home view
def HomeView(request):
    items = Items.objects.all()
    list = ItemList.objects.all()
    review = Feedback.objects.all()
    return render(request, 'home.html', {'items': items, 'list': list, 'review': review})

# About view
def AboutView(request):
    data = AboutUs.objects.all()
    return render(request, 'about.html', {'data': data})

# Read keywords from file

def read_keywords_from_file(filename):
    try:
        with open(filename, 'r') as file:
            keywords = file.read().splitlines()
        return keywords
    except Exception as e:
        print(f"Error reading keywords from file: {e}")
        return []

# Frequency threshold for keyword classification
FREQUENCY_THRESHOLD = 5  # Example threshold, adjust as needed

# Fetch URLs from Google Custom Search API
def fetch_urls_from_api(query, num_results=10):
    API_KEY = ''
    CSE_ID = ''
    url = " "
    params = {
        'key': API_KEY,
        'cx': CSE_ID,
        'q': query,
        'num': num_results,
        'start': 1  # Ensure fetching starts from the first result
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json().get('items', [])
        urls = [result['link'] for result in results]
        return urls
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URLs from API: {e}")
        return []

# Extract data from a URL
def extract_data(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        text = soup.get_text().lower()
        words = re.findall(r'\w+', text)
        word_freq = {word: words.count(word) for word in set(words)}
        
        urls = [a['href'] for a in soup.find_all('a', href=True)]
        
        hidden_text = ' '.join([tag.text for tag in soup.find_all(style=re.compile(r'display:\s*none'))])
        
        redirects = []
        for meta in soup.find_all('meta', attrs={"http-equiv": "refresh"}):
            content = meta.get('content')
            if content:
                redirect_url = re.search(r'url=(.*)', content)
                if redirect_url:
                    redirects.append(redirect_url.group(1))
        
        return {
            'url': url,
            'text': text,
            'word_freq': word_freq,
            'urls': urls,
            'hidden_text': hidden_text,
            'redirects': redirects
        }
    except Exception as e:
        print(f"Error extracting data from {url}: {e}")
        return None

# Classify website based on extracted data and keywords
def classify_website(data, keywords):
    poisoned_keywords = {keyword: data['word_freq'].get(keyword, 0) for keyword in keywords}
    poisoned_freq = sum(1 for freq in poisoned_keywords.values() if freq > FREQUENCY_THRESHOLD)
    poisoned = poisoned_freq > 0
    
    return {
        'url': data['url'],
        'poisoned_keywords': list(poisoned_keywords.keys()),
        'frequency_of_poisoned_keywords': list(poisoned_keywords.values()),
        'hidden_text': data['hidden_text'],
        'redirects': data['redirects'],
        'poisoned': poisoned,
        'message': 'Site is poisoned and not safe' if poisoned else 'Site is safe',
        'label': 'Poisoned' if poisoned else 'Safe'
    }


# Save results to a CSV file
def save_results(data, directory='output_directory'):
    try:
        os.makedirs(directory, exist_ok=True)
        
        output_path = os.path.join(directory, 'output.csv')
        
        df = pd.DataFrame([data])
        
        if os.path.exists(output_path):
            df.to_csv(output_path, mode='a', header=False, index=False)
        else:
            df.to_csv(output_path, index=False)
        
        print(f'Data saved to {output_path}')
    except Exception as e:
        print(f'Error saving results: {e}')

# Menu view
def MenuView(request):
    query = request.GET.get('query', '')
    results = []
    safe_count = 0
    poisoned_count = 0

    if query:
        keywords_file = 'keywords.txt'
        POISONED_KEYWORDS = read_keywords_from_file(keywords_file)

        urls = fetch_urls_from_api(query, num_results=10)
        for url in urls:
            data = extract_data(url)
            if data:
                result = classify_website(data, POISONED_KEYWORDS)
                results.append(result)
                if result['poisoned']:
                    poisoned_count += 1
                else:
                    safe_count += 1
                save_results(result)

    return render(request, 'menu.html', {
        'query': query,
        'results': results,
        'safe_count': safe_count,
        'poisoned_count': poisoned_count
    })

# Feedback view
def FeedbackView(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('feedback')  # Redirect to the feedback page
    else:
        form = FeedbackForm()
    
    return render(request, 'feedback.html', {'form': form})

# View to display all feedbacks
def AllFeedbacksView(request):
    feedbacks = Feedback.objects.all()
    return render(request, 'all_feedbacks.html', {'feedbacks': feedbacks})
