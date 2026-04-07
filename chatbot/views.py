# chatbot/views.py
"""
Views for the chatbot API.
Handles chat messages and returns responses from the agent.
"""
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings
import sys
from pathlib import Path

# Add AI directory to path
ai_dir = Path(__file__).resolve().parent.parent / "AI"
sys.path.insert(0, str(ai_dir))

from AI.agent import create_agent


@login_required
@ensure_csrf_cookie
@require_http_methods(["POST"])
def chat(request):
    """
    Handle chat messages from authenticated users.
    Returns JSON response with agent's reply.
    """
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        
        if not message:
            return JsonResponse({
                'success': False,
                'error': 'Message is required'
            }, status=400)
        
        # Get user ID for authenticated operations
        user_id = request.user.id
        
        # Create agent instance with user context
        agent = create_agent(user_id=user_id)
        
        # Get chat history from session if available
        chat_history = request.session.get('chat_history', [])
        
        # Get response from agent (Inject user_id as the Redis session_id for infinite memory)
        response = agent.chat(message, chat_history=chat_history, session_id=f"user_{user_id}_chat")
        
        # Update chat history in session (keep last 10 messages for UI, Redis keeps infinite)
        chat_history.append({
            'user': message,
            'assistant': response
        })
        request.session['chat_history'] = chat_history[-10:]
        request.session.save()
        
        return JsonResponse({
            'success': True,
            'response': response
        })
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Chatbot Error: {str(e)}")
        print(f"Traceback: {error_trace}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@ensure_csrf_cookie
@require_http_methods(["POST"])
def clear_history(request):
    """
    Clear chat history for the current user.
    """
    try:
        if 'chat_history' in request.session:
            del request.session['chat_history']
            request.session.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Chat history cleared'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

