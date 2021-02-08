from django.shortcuts import render
from dictword.models import Dictword

import requests
import json
import os

from dotenv import load_dotenv

# Create your views here.
def home(request):
    
    current_user = request.user
    user_words = Dictword.objects.all().filter(user=current_user)


    if request.method == "POST":

        load_dotenv('.env')

        search_word = request.POST.get('searchWord')

        url = "https://wordsapiv1.p.rapidapi.com/words/" + search_word + "/definitions"

        headers = {
            'x-rapidapi-key': os.getenv('API_KEY'),
            'x-rapidapi-host': "wordsapiv1.p.rapidapi.com"
        }

        response = requests.request("GET", url, headers=headers)
        json_data = json.loads(response.text)

        first_meaning = json_data['definitions'][0]

        definition, partOfSpeech = first_meaning['definition'], first_meaning['partOfSpeech']

        Dictword.objects.create(
            user = current_user,
            word = search_word,
            definition = definition,
            partOfSpeech = partOfSpeech
        )


    return render( request, 'home/home.html', {'words':user_words} )