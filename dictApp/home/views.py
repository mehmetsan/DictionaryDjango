from django.shortcuts import render
from dictword.models import Dictword
from django.contrib.auth.models import User

import requests
import json
import os

from dotenv import load_dotenv


def get_data(search_word):
    # API Configuration
    url = "https://wordsapiv1.p.rapidapi.com/words/" + search_word + "/definitions"

    headers = {
        'x-rapidapi-key': os.getenv('API_KEY'),
        'x-rapidapi-host': "wordsapiv1.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers)
    json_data = json.loads(response.text)

    first_meaning = json_data['definitions'][0]

    # Storing only the definition and part of speech
    definition, part_of_speech = first_meaning['definition'], first_meaning['partOfSpeech']

    return definition, part_of_speech

def global_check(word):
    all_words = Dictword.objects.all()
    global_dict_check = all_words.all().filter(word=word)

    return global_dict_check[0] if global_dict_check else False


# Create your views here.
def home(request):
    
    current_user = User.objects.all().filter(username=request.user.username)[0]
    all_words = Dictword.objects.all()
    user_words = all_words.filter(user=current_user).order_by('-id')
    practice = True if len(user_words) > 9 else False

    if request.method == "POST":

        #  Using environment variables for API KEY
        load_dotenv('.env')

        search_word = request.POST.get('search_word')

        global_dict_check = global_check(search_word)

        # If searching a new word
        if search_word:
            definition, part_of_speech = "", ""

            if global_dict_check:
                definition = global_dict_check.definition
                part_of_speech = global_dict_check.part_of_speech
            else:
                definition, part_of_speech = get_data(search_word)

            # Convert definition to one sentence to store its value in hidden input
            def_one_word = definition.replace(' ','-')

            # For displaying the Searched Word information
            word_data = {
                'word' : search_word.capitalize(),
                'definition' : definition.capitalize(),
                'part_of_speech' : part_of_speech.capitalize()
            }
            return render( request, 'home/home.html', {'words':user_words, 'made_a_search':True, "query":word_data, "def_one_word":def_one_word, 'practice':practice} )

        # If saving the word
        elif( request.POST.get('word') ):

            word = request.POST.get('word')
            global_dict_check = all_words.filter(word=word)

            # If the word is not present in the whole dictionary
            if not global_dict_check:
                dict_word = Dictword(
                    word = request.POST.get('word'),
                    definition = request.POST.get('definition').replace('-',' '),
                    part_of_speech = request.POST.get('part_of_speech')
                )
                # Save first to add user relationship
                dict_word.save()
                dict_word.user.add(current_user)
            # If word is in the dictionary
            else:
                user_dict_check = user_words.filter(word=word)

                # If word is not in the user's dictionary
                if not user_dict_check:
                    global_dict_check.user.add(current_user)

            # Update user words
            user_words = all_words.filter(user=current_user).order_by('-id')
            # Update Practice availability
            practice = True if len(user_words) > 9 else False

            return render( request, 'home/home.html', {'words':user_words, 'made_a_search':False, "query":None, 'practice': practice} )
        
    # If the user click 'Clear'    
    return render( request, 'home/home.html', {'words':user_words, 'made_a_search':False, "query":None, 'practice': practice} )
