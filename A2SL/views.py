from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import nltk
from django.contrib.staticfiles import finders
from googletrans import Translator  # ✅ Added for translation


# Optional but recommended to download in advance
# nltk.download('punkt')
# nltk.download('averaged_perceptron_tagger')
# nltk.download('wordnet')

def home_view(request):
    return render(request, 'home.html')

def about_view(request):
    return render(request, 'about.html')

def contact_view(request):
    return render(request, 'contact.html')

@login_required(login_url="login")
def animation_view(request):
    if request.method == 'POST':
        text = request.POST.get('sen', '').strip().lower()
        original_words = word_tokenize(text)

        # POS tagging
        tagged = nltk.pos_tag(original_words)

        # Tense detection
        tense = {"future": 0, "present": 0, "past": 0, "present_continuous": 0}
        for word, tag in tagged:
            if tag == "MD":
                tense["future"] += 1
            elif tag in ["VBP", "VBZ", "VBG"]:
                tense["present"] += 1
            elif tag in ["VBD", "VBN"]:
                tense["past"] += 1
            if tag == "VBG":
                tense["present_continuous"] += 1

        lr = WordNetLemmatizer()
        filtered_text = []

        for word, pos in tagged:
            if word in ["my", "name", "is"]:
                filtered_text.append(word)  # Don't lemmatize these
            elif pos in ['VBG', 'VBD', 'VBZ', 'VBN', 'VB']:
                filtered_text.append(lr.lemmatize(word, pos='v'))
            elif pos in ['JJ', 'JJR', 'JJS', 'RBR', 'RBS']:
                filtered_text.append(lr.lemmatize(word, pos='a'))
            elif pos.startswith('NN') or pos == 'PRP':
                filtered_text.append(word)
            else:
                filtered_text.append(lr.lemmatize(word))

        # Add tense marker
        probable_tense = max(tense, key=tense.get)
        if probable_tense == "past" and tense["past"] >= 1:
            filtered_text.insert(0, "Before")
        elif probable_tense == "future" and tense["future"] >= 1:
            if "will" not in filtered_text:
                filtered_text.insert(0, "Will")
        elif probable_tense == "present" and tense["present_continuous"] >= 1:
            filtered_text.insert(0, "Now")

        # Prepare final animation word list
        final_words = []
        for word in filtered_text:
            word_path = f"assets/{word}.mp4"
            if finders.find(word_path):
                final_words.append(word)
            else:
                for letter in word:
                    letter_path = f"assets/{letter}.mp4"
                    if finders.find(letter_path):
                        final_words.append(letter)

        return render(request, 'animation.html', {
            'words': final_words,
            'text': text
        })

    return render(request, 'animation.html')

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('animation')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            return redirect('animation')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect("home")


# ✅ NEW: Translate any language to English
def translate_view(request):
    text = request.GET.get('text', '')
    translator = Translator()
    translated = translator.translate(text, dest='en')
    return JsonResponse({'translated': translated.text})