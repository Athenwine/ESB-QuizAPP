# quiz/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('quiz/<int:pk>/', views.quiz_detail, name='quiz_detail'),
    path('quiz/<int:pk>/scores/', views.quiz_scores, name='quiz_scores'),
    
    # Quiz taking
    path('quiz/<int:pk>/start/', views.start_quiz, name='start_quiz'),
    path('attempt/<int:attempt_id>/take/', views.take_quiz, name='take_quiz'),
    path('attempt/<int:attempt_id>/result/', views.quiz_result, name='quiz_result'),
    
    # Quiz creation and management
    path('create/', views.create_quiz, name='create_quiz'),
    path('quiz/<int:quiz_id>/add-question/', views.add_question, name='add_question'),
    path('quiz/<int:pk>/delete/', views.delete_quiz, name='delete_quiz'),
    
    # User dashboard
    path('my-quizzes/', views.my_quizzes, name='my_quizzes'),
    path('my-results/', views.my_results, name='my_results'),
    
    # Team page
    path('team/', views.team, name='team'),
    
    # Authentication
    path('register/', views.register, name='register'),
]