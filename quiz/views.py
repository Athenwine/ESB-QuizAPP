# quiz/views.py - REMPLACEZ TOUT LE CONTENU
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count
from .models import Quiz, Question, Choice, QuizAttempt, Answer
from .forms import QuizForm, QuestionForm, ChoiceForm


def home(request):
    """Page d'accueil avec liste des quiz"""
    quizzes = Quiz.objects.filter(is_active=True).annotate(
        questions_count=Count('questions'),
        attempts_count=Count('attempts')
    )
    context = {'quizzes': quizzes}
    return render(request, 'quiz/home.html', context)


def quiz_detail(request, pk):
    """Détails d'un quiz"""
    quiz = get_object_or_404(Quiz, pk=pk, is_active=True)
    questions_count = quiz.get_questions_count()
    
    previous_attempts = None
    if request.user.is_authenticated:
        previous_attempts = QuizAttempt.objects.filter(
            user=request.user, 
            quiz=quiz, 
            is_completed=True
        ).order_by('-completed_at')
    
    context = {
        'quiz': quiz,
        'questions_count': questions_count,
        'previous_attempts': previous_attempts,
    }
    return render(request, 'quiz/quiz_detail.html', context)


@login_required
def start_quiz(request, pk):
    """Démarrer un nouveau quiz"""
    quiz = get_object_or_404(Quiz, pk=pk, is_active=True)
    attempt = QuizAttempt.objects.create(user=request.user, quiz=quiz)
    return redirect('take_quiz', attempt_id=attempt.id)


@login_required
def take_quiz(request, attempt_id):
    """Passer un quiz"""
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user, is_completed=False)
    questions = attempt.quiz.questions.all().prefetch_related('choices')
    
    if request.method == 'POST':
        score = 0
        
        for question in questions:
            selected_choice_ids = request.POST.getlist(f'question_{question.id}')
            answer = Answer.objects.create(attempt=attempt, question=question)
            
            if selected_choice_ids:
                selected_choices = Choice.objects.filter(id__in=selected_choice_ids)
                answer.selected_choices.set(selected_choices)
                
                correct_choices = question.choices.filter(is_correct=True)
                selected_correct = selected_choices.filter(is_correct=True)
                
                if (correct_choices.count() == selected_correct.count() and 
                    selected_choices.count() == correct_choices.count()):
                    answer.is_correct = True
                    score += question.points
                    answer.save()
        
        attempt.score = score
        attempt.is_completed = True
        attempt.completed_at = timezone.now()
        attempt.save()
        
        messages.success(request, f'Quiz terminé! Votre score: {score}/{attempt.quiz.get_max_score()}')
        return redirect('quiz_result', attempt_id=attempt.id)
    
    context = {
        'attempt': attempt,
        'questions': questions,
    }
    return render(request, 'quiz/take_quiz.html', context)


@login_required
def quiz_result(request, attempt_id):
    """Résultats d'un quiz"""
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user, is_completed=True)
    answers = attempt.answers.all().prefetch_related('selected_choices', 'question__choices')
    
    context = {
        'attempt': attempt,
        'answers': answers,
        'percentage': attempt.get_percentage(),
    }
    return render(request, 'quiz/quiz_result.html', context)


@login_required
def create_quiz(request):
    """Créer un nouveau quiz"""
    if request.method == 'POST':
        form = QuizForm(request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.created_by = request.user
            quiz.save()
            messages.success(request, 'Quiz créé avec succès! Ajoutez maintenant des questions.')
            return redirect('add_question', quiz_id=quiz.id)
    else:
        form = QuizForm()
    
    context = {'form': form}
    return render(request, 'quiz/create_quiz.html', context)


@login_required
def add_question(request, quiz_id):
    """Ajouter des questions à un quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id, created_by=request.user)
    
    if request.method == 'POST':
        question_form = QuestionForm(request.POST)
        if question_form.is_valid():
            question = question_form.save(commit=False)
            question.quiz = quiz
            question.save()
            
            choice_texts = request.POST.getlist('choice_text[]')
            is_correct_list = request.POST.getlist('is_correct[]')
            
            for i, choice_text in enumerate(choice_texts):
                if choice_text.strip():
                    Choice.objects.create(
                        question=question,
                        choice_text=choice_text,
                        is_correct=str(i) in is_correct_list
                    )
            
            messages.success(request, 'Question ajoutée avec succès!')
            return redirect('add_question', quiz_id=quiz.id)
    else:
        question_form = QuestionForm()
    
    questions = quiz.questions.all().prefetch_related('choices')
    
    context = {
        'quiz': quiz,
        'question_form': question_form,
        'questions': questions,
    }
    return render(request, 'quiz/add_question.html', context)


@login_required
def my_quizzes(request):
    """Liste des quiz créés par l'utilisateur"""
    quizzes = Quiz.objects.filter(created_by=request.user).annotate(
        questions_count=Count('questions'),
        attempts_count=Count('attempts')
    )
    context = {'quizzes': quizzes}
    return render(request, 'quiz/my_quizzes.html', context)


@login_required
def my_results(request):
    """Historique des résultats de l'utilisateur"""
    attempts = QuizAttempt.objects.filter(
        user=request.user, 
        is_completed=True
    ).select_related('quiz').order_by('-completed_at')
    
    context = {'attempts': attempts}
    return render(request, 'quiz/my_results.html', context)


def quiz_scores(request, pk):
    """Classement d'un quiz"""
    quiz = get_object_or_404(Quiz, pk=pk)
    scores = QuizAttempt.objects.filter(
        quiz=quiz, 
        is_completed=True
    ).select_related('user').order_by('-score', 'completed_at')[:10]
    
    context = {
        'quiz': quiz,
        'scores': scores,
    }
    return render(request, 'quiz/quiz_scores.html', context)


@login_required
def delete_quiz(request, pk):
    """Supprimer un quiz"""
    quiz = get_object_or_404(Quiz, pk=pk, created_by=request.user)
    if request.method == 'POST':
        quiz.delete()
        messages.success(request, 'Quiz supprimé avec succès!')
        return redirect('my_quizzes')
    
    context = {'quiz': quiz}
    return render(request, 'quiz/delete_quiz.html', context)


def register(request):
    """Inscription d'un nouvel utilisateur"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, 'Compte créé avec succès! Bienvenue!')
            return redirect('home')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})


def team(request):
    """Page de présentation de l'équipe"""
    team_members = [
        {
            'name': 'Aws Ourari',
            'role': 'Lead Developer & Backend',
            'photo': 'images/team/aws.jpg',
            'description': 'Responsable du développement backend et de l\'architecture du projet.',
            'skills': ['Django', 'Python', 'Database Design', 'API Development']
        },
        {
            'name': 'Najla Nairi',
            'role': 'Frontend Developer & UX Designer',
            'photo': 'images/team/najla.jpg',
            'description': 'En charge du design de l\'interface utilisateur et de l\'expérience utilisateur.',
            'skills': ['HTML/CSS', 'Bootstrap', 'UI/UX Design', 'Responsive Design']
        },
        {
            'name': 'Ines Jaziri',
            'role': 'Full Stack Developer & Tester',
            'photo': 'images/team/ines.jpg',
            'description': 'Développement full-stack et tests de l\'application.',
            'skills': ['Django', 'JavaScript', 'Testing', 'Quality Assurance']
        }
    ]
    
    context = {'team_members': team_members}
    return render(request, 'quiz/team.html', context)