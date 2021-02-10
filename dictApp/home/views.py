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

'''
    Helper function for API call to WordsAPI

    Takes a word to search (String) as parameter

    Returns the definition and part of speach of the inputted word
'''
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

'''
    A helper method for local dictionary search

    Takes a word (String) as input

    Returns Dictword model instance of the inputted word if its in the dictionary

    Else, returns False
'''
def global_check(word):
    all_words = Dictword.objects.all()
    global_dict_check = all_words.filter(word=word.capitalize())
    return global_dict_check[0] if global_dict_check else False

'''
    A helper method for updating the score attributes of the words

    Takes a list of words Dictword objects and User instance

    Calculates and updates the new score according to the formula

    Returns None
'''
def update_powers( words, current_user ):
    for each in words:
        interaction_obj = Interaction.objects.all().filter(word=each, user=current_user)
        appear_count = interaction_obj[0].appear_count
        search_count = interaction_obj[0].search_count
        points = interaction_obj[0].points

        power = (points / sqrt(appear_count) ) + search_count / 5
        interaction_obj.update(power=power)
    return

'''
    Helper function for gathering display informations for User words

    Takes a list of User's dictwords and the User instance as input

    For each word, generates a list of Dictword object, Interaction object, and color

    Decides on the color based on the Interaction's the power

    Returns the list of generated lists
'''
def get_powers( words, current_user ):
    powers = []
    for each in words:
        word_obj = Dictword.objects.get(word=each.word)
        interaction_obj = Interaction.objects.get(word=each, user=current_user)
     
        # Decide on the display color
        power = interaction_obj.power
        color = ""

        if power >= 5:
            color = 'greenyellow'
        elif power >= 2:
            color = 'yellow'
        else:
            color = 'red'

        powers.append([word_obj, interaction_obj.power, color ])
    return powers

'''
    Helper function for searching a word

    Takes request, searched word (String) and list of User's Dictwords

    First searches the word in the locally downloaded data

    Uses API call if the word is not available in database

    Shows page with error message if the API call fails

    Else shows search query results on the page

'''
def search_new(request, search_word, user_words):
    load_dotenv('.env')
    global_dict_check = global_check(search_word)
    user_dict_check = user_words.filter(word=search_word)
    display = get_powers( list(user_words) , request.user )
    definition, part_of_speech = "", ""
    practice = True if len(user_words) > 9 else False
    not_found = False

    # If the word is already in the database
    if global_dict_check:
        definition = global_dict_check.definition
        part_of_speech = global_dict_check.part_of_speech

        # Update interaction if the word is in user's dictionary
        if user_dict_check:
            interaction = Interaction.objects.all().filter(word=user_dict_check[0], user=request.user)
            search_count = interaction[0].search_count
            interaction.update(search_count = search_count + 1)

    # If we need an API call
    else:
        definition, part_of_speech = get_data(search_word)
        # If the entered word lookup failed
        if not definition:
            not_found = True
            return render( request, 'home/home.html', {'words':display, 'made_a_search':True, 'practice':practice, 'not_found':not_found} )

    # Convert definition to one sentence to store its value in hidden input
    def_one_word = definition.replace(' ','-')

    # For displaying the Searched Word information
    word_data = {
        'word' : search_word.capitalize(),
        'definition' : definition.capitalize(),
        'part_of_speech' : part_of_speech.capitalize()
    }
    
    return render( request, 'home/home.html', {'words':display, 'made_a_search':True, "query":word_data, "def_one_word":def_one_word, 'practice':practice, 'not_found':False} )

'''
    Helper function for saving a searched word

    Takes request, searched word (String) and list of User's Dictwords

    Adds the word to the database if it is not already in it 

    If the word is in the database, checks whether it is in the User's dictionary

    If it is not, adds User to the Dictword's users

    Then checks whether user has a Instance of the word

    If it is not, creates and adds and Instance

    Returns the upadeted view 

'''
def save_word(request, search_word, user_words):
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
        dict_word.user.add(request.user)
        created_word = dict_word

    # If word is in the dictionary
    else:
        created_word = global_dict_check
        # If word is not in the user's dictionary
        if not user_dict_check:
            global_dict_check.user.add(request.user)

    inter_check = Interaction.objects.all().filter(user=request.user, word=created_word)        
    if not inter_check:
        # Create a score for user - word
        Interaction.objects.create(
            user=request.user,
            word=created_word,
            points = 0,
            search_count = 1,
            appear_count = 1,
            power = 0
        )

    # Update user words
    user_words = Dictword.objects.all().filter(user=request.user).order_by('-id')
    # Update Practice availability
    practice = True if len(user_words) > 9 else False

    display = get_powers( list(user_words) , request.user )
    return render( request, 'home/home.html', {'words':display, 'made_a_search':False, 'practice': practice} )

'''
    Helper funciton for removing a word

    Takes request and word to remove (Dictword) as inputs

    Deletes the Dictword object

    Updates User's words and practice eligibility 

    Returns the upadeted view
'''
def remove_word(request, remove_word):
    print("REMOVE WORD", remove_word)
    remove_word.user.remove(request.user)

    remove_interaction = Interaction.objects.all().filter(user=request.user, word=remove_word)
    remove_interaction.delete()

    # Update user words
    user_words = Dictword.objects.all().filter(user=request.user).order_by('-id')

    # Update Practice availability
    practice = True if len(user_words) > 9 else False

    user_words = get_powers( list(user_words) , request.user )
    return render( request, 'home/home.html', {'words':user_words, 'made_a_search':False, 'practice': practice} )

'''
    Helper function for updating a Interaction's score

    Takes request, a word (String), and a change amount

    Updates the power of the word by the change amount

    Returns None

'''
def update_score( request, word, change):
    changed_word = Dictword.objects.get(word=word)
    changed_word_inter = Interaction.objects.all().filter(user=request.user, word=changed_word)
    changed_word_points = changed_word_inter[0].points
    changed_word_inter.update(points=changed_word_points + change)
    return


'''
    Home view for the landing page

    Requires user login with a decorator

    Displays user words as default

    Returns rendered views based on the incoming POST request

'''
# Create your views here.
@login_required(login_url='/users/login')
def home(request):
    
    current_user = request.user
    all_words = Dictword.objects.all()
    user_words = all_words.filter(user=current_user).order_by('-id')
    practice = True if len(user_words) > 9 else False

    if request.method == "POST":

        search_word = request.POST.get('search_word')

        # If searching a new word
        if search_word:
            return search_new(request, search_word, user_words)

        # If saving the word
        elif( request.POST.get('word') ):
            return save_word(request, search_word, user_words)

        # If removing a word
        elif( request.POST.get('word_to_remove')):
            word_to_remove = global_check(request.POST.get('word_to_remove'))
            return remove_word(request, word_to_remove)

    # If the user click 'Clear'    
    display = get_powers( list(user_words) , current_user )

    return render( request, 'home/home.html', {'words':display, 'made_a_search':False, 'practice': practice } )


'''
    Practice view for the practicing page

    Requires User practice eligiblity, else redirects to landing page

    Selects a random definition and 3 word choices and displays them

    If the user gives an answer, evaluates the answer and makes the required score changes

    Returns the rendered practice page view
'''
@user_see_practice
def practice(request):

    # If an answer is given
    if request.method == "POST":
        question_cw = request.POST.get('question_cw')
        question_fw1 = request.POST.get('question_fw1')
        question_fw2 = request.POST.get('question_fw2')
        user_answer = request.POST.get('user_answer')

        # If correct answer is given
        if user_answer == question_cw:
            update_score(request,question_cw,3)

        # If wrong answer is given
        else:
            # Subtract from the correct answer
            update_score(request,question_cw,-2)

            # Subtract from first false word's points
            update_score(request,question_fw1,-1)

            # Subtract from second false word's points
            update_score(request,question_fw2,-1)


    # Get random words and a random definition
    user_words = Dictword.objects.all().filter(user=request.user)
    random_words = random.sample(list(user_words), 3)

    update_powers( list(user_words), request.user)

    # Update each word's appear counts
    for each in random_words:
        word_obj = Dictword.objects.all().filter(word=each)[0]
        interaction_obj = Interaction.objects.all().filter(word=word_obj, user=request.user)
        interaction_obj.update(appear_count = interaction_obj[0].appear_count + 1)
    
    random_definition = random_words[0].definition
    random_word = random_words[0].word
    false_word1 = random_words[1].word
    false_word2 = random_words[2].word

    # So that correct answer's place changes every time
    choices = [random_word, false_word1, false_word2 ]
    random.shuffle(choices)

    # For displaying the question on the practice page
    choices_dict = {
        'random_word' : random_word,
        'false_word1' : false_word1,
        'false_word2' : false_word2,
    }

    return render(request, 'home/practice.html', {'random_definition':random_definition, 'choices':choices, 'choices_dict':choices_dict})

