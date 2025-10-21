# Messaging Feature

This app provides messaging functionality for candidates and recruiters to communicate with each other.

## Features

- **Inbox**: View all conversations with unread message counts
- **Conversations**: Real-time conversation view with message history
- **Compose**: Send new messages to other users
- **Message Notifications**: Unread message badge in navigation
- **Profile Integration**: "Send Message" button on user profiles
- **Job Integration**: "Message Recruiter" button on job detail pages

## Models

### Message
- `sender`: User who sent the message
- `receiver`: User who receives the message
- `subject`: Message subject line
- `content`: Message body
- `timestamp`: When the message was sent
- `is_read`: Boolean flag for read/unread status
- `parent_message`: Optional reference to parent message for threading

## URLs

- `/messages/` - Inbox view (all conversations)
- `/messages/compose/` - Compose new message
- `/messages/compose/<username>/` - Compose message to specific user
- `/messages/conversation/<username>/` - View conversation with specific user
- `/messages/delete/<message_id>/` - Delete a message

## Usage

1. Users can access messages from the navigation bar
2. Unread message count is displayed as a badge
3. Users can message each other from:
   - User profiles
   - Job detail pages (to contact recruiters)
   - Direct compose page
4. All messages are organized by conversation
5. Messages are automatically marked as read when viewed

## Admin

Messages can be managed through the Django admin interface at `/admin/messaging/message/`

