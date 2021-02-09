from django.shortcuts import render
from django.http import JsonResponse
from dictword.models import Dictword, Interaction
from .decorators import user_see_practice
from django.contrib.auth.decorators import login_required

import requests
import json
import os
import random
from dotenv import load_dotenv
from math import sqrt

def get_data(search_word):
    # API Configuration
    url = "https://wordsapiv1.p.rapidapi.com/words/" + search_word + "/definitions"

    headers = {
        'x-rapidapi-key': os.getenv('API_KEY'),
        'x-rapidapi-host': "wordsapiv1.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers)
    json_data = json.loads(response.text)
    
    try:
        first_meaning = json_data['definitions'][0]

        # Storing only the definition and part of speech
        definition, part_of_speech = first_meaning['definition'], first_meaning['partOfSpeech']

    except:
        definition, part_of_speech = False, False

    return definition, part_of_speech

def global_check(word):
    all_words = Dictword.objects.all()
    global_dict_check = all_words.filter(word=word.capitalize())

    return global_dict_check[0] if global_dict_check else False

def update_score( words, current_user ):
    for each in words:
        interaction_obj = Interaction.objects.all().filter(word=each, user=current_user)
        appear_count = interaction_obj[0].appear_count
        search_count = interaction_obj[0].search_count
        points = interaction_obj[0].points

        power = (points / sqrt(appear_count) ) + search_count / 5
        interaction_obj.update(power=power)
    return

def get_powers( words, current_user ):
    powers = []
    for each in words:
        word_obj = Dictword.objects.get(word=each)
        interaction_obj = Interaction.objects.get(word=each, user=current_user)
     
        appear_count = interaction_obj.appear_count
        search_count = interaction_obj.search_count
        power = interaction_obj.power

        color = ""

        if power >= 5:
            color = 'greenyellow'
        elif power >= 2:
            color = 'yellow'
        else:
            color = 'red'


        powers.append([word_obj, interaction_obj.power, color, appear_count, search_count, power])
    return powers

# Create your views here.
@login_required(login_url='/users/login')
def home(request):
    
    current_user = request.user
    all_words = Dictword.objects.all()
    user_words = all_words.filter(user=current_user).order_by('-id')
    practice = True if len(user_words) > 9 else False

    if request.method == "POST":

        #  Using environment variables for API KEY
        load_dotenv('.env')

        search_word = request.POST.get('search_word')

        # If searching a new word
        if search_word:
            global_dict_check = global_check(search_word)
            user_dict_check = user_words.filter(word=search_word)

            definition, part_of_speech = "", ""

            # If the word is already in the database
            if global_dict_check:
                definition = global_dict_check.definition
                part_of_speech = global_dict_check.part_of_speech

                # Update interaction if the word is in user's dictionary
                if user_dict_check:
                    interaction = Interaction.objects.all().filter(word=user_dict_check[0], user=current_user)
                    search_count = interaction[0].search_count
                    interaction.update(search_count = search_count + 1)

            # If we need an API call
            else:
                definition, part_of_speech = get_data(search_word)
                if not definition:
                    user_words = get_powers( list(user_words) , request.user )
                    return render( request, 'home/home.html', {'words':user_words, 'made_a_search':True, 'practice':practice, 'not_found':True} )

            # Convert definition to one sentence to store its value in hidden input
            def_one_word = definition.replace(' ','-')

            # For displaying the Searched Word information
            word_data = {
                'word' : search_word.capitalize(),
                'definition' : definition.capitalize(),
                'part_of_speech' : part_of_speech.capitalize()
            }
            user_words = get_powers( list(user_words) , request.user )
            return render( request, 'home/home.html', {'words':user_words, 'made_a_search':True, "query":word_data, "def_one_word":def_one_word, 'practice':practice} )

        # If saving the word
        elif( request.POST.get('word') ):

            word = request.POST.get('word')
            global_dict_check = global_check(word)
            user_dict_check = user_words.filter(word=search_word)
            created_word = ""

            # If the word is not present in the whole dictionary
            if not global_dict_check:
                dict_word = Dictword(
                    word = request.POST.get('word'),
                    definition = request.POST.get('definition').replace('-',' ').capitalize(),
                    part_of_speech = request.POST.get('part_of_speech')
                )
                # Save first to add user relationship
                dict_word.save()
                dict_word.user.add(current_user)
                created_word = dict_word

            # If word is in the dictionary
            else:
                created_word = global_dict_check
                # If word is not in the user's dictionary
                if not user_dict_check:
                    global_dict_check.user.add(current_user)
                    
            # Create a score for user - word
            Interaction.objects.create(
                user=current_user,
                word=created_word,
                points = 0,
                search_count = 1,
                appear_count = 1,
                power = 0
            )

            # Update user words
            user_words = all_words.filter(user=current_user).order_by('-id')
            # Update Practice availability
            practice = True if len(user_words) > 9 else False

            user_words = get_powers( list(user_words) , request.user )
            return render( request, 'home/home.html', {'words':user_words, 'made_a_search':False, "query":None, 'practice': practice} )
        
        # If removing a word
        elif( request.POST.get('word_to_remove')):
            remove_word = global_check(request.POST.get('word_to_remove'))
            remove_word.user.remove(current_user)

            remove_interaction = Interaction.objects.all().filter(user=current_user, word=remove_word)
            remove_interaction.delete()
            # Update user words
            user_words = all_words.filter(user=current_user).order_by('-id')

            # Update Practice availability
            practice = True if len(user_words) > 9 else False

            user_words = get_powers( list(user_words) , request.user )
            return render( request, 'home/home.html', {'words':user_words, 'made_a_search':False, "query":None, 'practice': practice} )

    user_words = get_powers( list(user_words) , request.user )
    # If the user click 'Clear'    
    return render( request, 'home/home.html', {'words':user_words, 'made_a_search':False, "query":None, 'practice': practice, "word_stats":list(all_words.filter(user=current_user).order_by('-id'))} )

@user_see_practice
def practice(request):

    # If an answer is given
    if request.method == "POST":
        question_cw = request.POST.get('question_cw')
        question_fw1 = request.POST.get('question_fw1')
        question_fw2 = request.POST.get('question_fw2')
        user_answer = request.POST.get('user_answer')

        # Correct answer given
        if user_answer == question_cw:
            cw_word = Dictword.objects.get(word=question_cw)
            cw_score = Interaction.objects.all().filter(user=request.user, word=cw_word)
            cw_points = cw_score[0].points
            cw_score.update(points=cw_points + 4)

        # Wrong answer given
        else:
            # Subtract from the correct answer
            cw_word = Dictword.objects.get(word=question_cw)
            cw_score = Interaction.objects.all().filter(user=request.user, word=cw_word)
            cw_points = cw_score[0].points
            cw_score.update(points=cw_points - 2)

            # Subtract from first false word's points
            fw1_word = Dictword.objects.get(word=question_fw1)
            fw1_score = Interaction.objects.all().filter(user=request.user, word=fw1_word)
            fw1_points = fw1_score[0].points
            fw1_score.update(points=fw1_points - 1)

            # Subtract from second false word's points
            fw2_word = Dictword.objects.get(word=question_fw2)
            fw2_score = Interaction.objects.all().filter(user=request.user, word=fw2_word)
            fw2_points = fw2_score[0].points
            fw2_score.update(points=fw2_points - 1)

    # Get random words and a random definition
    user_words = Dictword.objects.all().filter(user=request.user)
    random_words = random.sample(list(user_words), 3)

    update_score( list(user_words), request.user)

    # Update each word's appear counts
    for each in random_words:
        word_obj = Dictword.objects.all().filter(word=each)[0]
        interaction_obj = Interaction.objects.all().filter(word=word_obj, user=request.user)
        interaction_obj.update(appear_count = interaction_obj[0].appear_count + 1)
    
    random_definition = random_words[0].definition
    random_word = random_words[0].word
    false_word1 = random_words[1].word
    false_word2 = random_words[2].word

    # So that correct answer changes every time
    choices = [random_word, false_word1, false_word2 ]
    random.shuffle(choices)

    # For displaying the question on the practice page
    choices_dict = {
        'random_word' : random_word,
        'false_word1' : false_word1,
        'false_word2' : false_word2,
    }

    return render(request, 'home/practice.html', {'random_definition':random_definition, 'choices':choices, 'choices_dict':choices_dict})

