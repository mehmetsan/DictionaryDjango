from django.shortcuts import render
from dictword.models import Dictword
from django.contrib.auth.models import User

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

        search_word = request.POST.get('search_word')

        # IF SEARCHING A NEW WORD
        if search_word:

            url = "https://wordsapiv1.p.rapidapi.com/words/" + search_word + "/definitions"

            headers = {
                'x-rapidapi-key': os.getenv('API_KEY'),
                'x-rapidapi-host': "wordsapiv1.p.rapidapi.com"
            }

            response = requests.request("GET", url, headers=headers)
            json_data = json.loads(response.text)

            first_meaning = json_data['definitions'][0]

            definition, partOfSpeech = first_meaning['definition'].capitalize(), first_meaning['partOfSpeech']

            def_one_word = definition.replace(' ','-')

            dict_word = Dictword(
                user = current_user,
                word = search_word,
                definition = definition,
                partOfSpeech = partOfSpeech
            )
            
            return render( request, 'home/home.html', {'words':user_words, 'made_a_search':True, "query":dict_word, "def_one_word":def_one_word} )

        # IF SAVING THE WORD
        elif( request.POST.get('user') ):
            Dictword.objects.create(
                user = request.user,
                word = request.POST.get('word'),
                definition = request.POST.get('definition').replace('-',' '),
                partOfSpeech = request.POST.get('partOfSpeech')
            )
            return render( request, 'home/home.html', {'words':user_words, 'made_a_search':False, "query":None} )
        
    return render( request, 'home/home.html', {'words':user_words, 'made_a_search':False, "query":None} )
