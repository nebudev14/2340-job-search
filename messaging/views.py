from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages as django_messages
from django.db.models import Q, Max, OuterRef, Subquery
from .models import Message
from .forms import MessageForm, ReplyForm


@login_required
def inbox(request):
    """Display all conversations for the current user"""
    user = request.user
    
    # Get the latest message for each conversation
    latest_message_subquery = Message.objects.filter(
        Q(sender=user, receiver=OuterRef('other_user')) |
        Q(receiver=user, sender=OuterRef('other_user'))
    ).order_by('-timestamp').values('timestamp')[:1]
    
    # Get all users the current user has conversations with
    sent_to = Message.objects.filter(sender=user).values_list('receiver', flat=True).distinct()
    received_from = Message.objects.filter(receiver=user).values_list('sender', flat=True).distinct()
    conversation_user_ids = set(sent_to) | set(received_from)
    
    conversations = []
    for user_id in conversation_user_ids:
        other_user = User.objects.get(id=user_id)
        
        # Get latest message in this conversation
        latest_msg = Message.objects.filter(
            Q(sender=user, receiver=other_user) |
            Q(receiver=user, sender=other_user)
        ).order_by('-timestamp').first()
        
        # Count unread messages from this user
        unread_count = Message.objects.filter(
            sender=other_user,
            receiver=user,
            is_read=False
        ).count()
        
        conversations.append({
            'user': other_user,
            'latest_message': latest_msg,
            'unread_count': unread_count
        })
    
    # Sort by latest message timestamp
    conversations.sort(key=lambda x: x['latest_message'].timestamp, reverse=True)
    
    context = {
        'conversations': conversations
    }
    return render(request, 'messaging/inbox.html', context)


@login_required
def conversation(request, username):
    """Display conversation with a specific user"""
    other_user = get_object_or_404(User, username=username)
    user = request.user
    
    # Get all messages in this conversation
    conversation_messages = Message.objects.filter(
        Q(sender=user, receiver=other_user) |
        Q(receiver=user, sender=other_user)
    ).order_by('timestamp')
    
    # Mark all messages from the other user as read
    Message.objects.filter(
        sender=other_user,
        receiver=user,
        is_read=False
    ).update(is_read=True)
    
    # Handle reply form submission
    if request.method == 'POST':
        form = ReplyForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = user
            message.receiver = other_user
            
            # Get subject from the first message in the conversation
            first_message = conversation_messages.first()
            if first_message:
                message.subject = f"Re: {first_message.subject}"
            else:
                message.subject = "Re: Conversation"
            
            message.save()
            django_messages.success(request, 'Message sent successfully!')
            return redirect('messaging.conversation', username=username)
    else:
        form = ReplyForm()
    
    context = {
        'other_user': other_user,
        'conversation_messages': conversation_messages,
        'form': form
    }
    return render(request, 'messaging/conversation.html', context)


@login_required
def compose(request, username=None):
    """Compose a new message"""
    initial_data = {}
    
    if username:
        receiver = get_object_or_404(User, username=username)
        initial_data['receiver'] = receiver
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            django_messages.success(request, 'Message sent successfully!')
            return redirect('messaging.conversation', username=message.receiver.username)
    else:
        form = MessageForm(initial=initial_data)
    
    # Get all users except the current user for the dropdown
    form.fields['receiver'].queryset = User.objects.exclude(id=request.user.id).order_by('username')
    
    context = {
        'form': form
    }
    return render(request, 'messaging/compose.html', context)


@login_required
def delete_message(request, message_id):
    """Delete a message"""
    message = get_object_or_404(Message, id=message_id)
    
    # Only allow sender or receiver to delete
    if request.user == message.sender or request.user == message.receiver:
        message.delete()
        django_messages.success(request, 'Message deleted successfully!')
    else:
        django_messages.error(request, 'You do not have permission to delete this message.')
    
    return redirect('messaging.inbox')
