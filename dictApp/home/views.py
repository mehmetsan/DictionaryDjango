from django.shortcuts import render
from dictword.models import Dictword
from django.contrib.auth.models import User

import requests
import json
import os

from dotenv import load_dotenv

# Create your views here.
def home(request):
    
    current_user = User.objects.all().filter(username=request.user.username)[0]
    all_words = Dictword.objects.all()
    user_words = all_words.filter(user=current_user)


    if request.method == "POST":

        #  USING ENVIRONMENT VARIABLE FOR API KEY
        load_dotenv('.env')

        search_word = request.POST.get('search_word')

        # IF SEARCHING A NEW WORD
        if search_word:

            # API CONFIGURATION
            url = "https://wordsapiv1.p.rapidapi.com/words/" + search_word + "/definitions"

            headers = {
                'x-rapidapi-key': os.getenv('API_KEY'),
                'x-rapidapi-host': "wordsapiv1.p.rapidapi.com"
            }

            response = requests.request("GET", url, headers=headers)
            json_data = json.loads(response.text)

            first_meaning = json_data['definitions'][0]

            # STORING ONLY THE DEFINITION AND THE PART OF SPEECH
            definition, partOfSpeech = first_meaning['definition'], first_meaning['partOfSpeech']

            # CONVERT INTO ONE SENTENCE, SO THAT IT CAN BE STORED IN THE HIDDEN INPUT FIELD
            def_one_word = definition.replace(' ','-')

            # FOR DISPLAYING THE SEARCHED WORD INFO
            word_data = {
                'word' : search_word.capitalize(),
                'definition' : definition.capitalize(),
                'partOfSpeech' : partOfSpeech.capitalize()
            }
            
            return render( request, 'home/home.html', {'words':user_words, 'made_a_search':True, "query":word_data, "def_one_word":def_one_word} )

        # IF SAVING THE WORD
        elif( request.POST.get('word') ):

            word = request.POST.get('word')
            global_dict_check = all_words.filter(word=word)

            # IF THE WORD IS NOT PRESENT IN THE WHOLE DICTIONARY
            if not global_dict_check:
                dict_word = Dictword(
                    word = request.POST.get('word'),
                    definition = request.POST.get('definition').replace('-',' '),
                    partOfSpeech = request.POST.get('partOfSpeech')
                )
                dict_word.save()
                dict_word.user.add(current_user)
            # IF WORD IS IN DICTIONARY, BUT JUST NOT IN USER'S
            else:
                user_dict_check = user_words.filter(word=word)

                if not user_dict_check:
                    global_dict_check.user.add(current_user)

            return render( request, 'home/home.html', {'words':user_words, 'made_a_search':False, "query":None} )
        
    # IF THE USER CLICKS CLEAR AND DOESN'T ADD THE WORD    
    return render( request, 'home/home.html', {'words':user_words, 'made_a_search':False, "query":None} )
