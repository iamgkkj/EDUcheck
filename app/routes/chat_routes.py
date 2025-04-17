from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from flask_socketio import emit
from app import socketio, db
# Use the correct import path for your models if they are not directly under app.models
from app.models.chat import Chat, ChatMessage 
from app.models.user import User # Assuming User model is here
from app.forms import ChatMessageForm # Removed NewChatForm as students don't need it
# from app.models import User # Already imported if User is in models/__init__.py or similar
from app.utils import role_required
from werkzeug.utils import secure_filename
from datetime import datetime
import os


bp = Blueprint('chat_routes', __name__, url_prefix='/chat') # Added url_prefix

@bp.route('/') # Now corresponds to /chat/
@login_required
def chat_interface():
    form = ChatMessageForm()
    active_chat = None

    # Get all chats for the current student user
    # Assuming student role check happens elsewhere or is implicit here
    chats = Chat.query.filter_by(student_id=current_user.id).join(User, Chat.teacher_id == User.id).all()

    # --- Add logic to calculate unread count per chat ---
    chats_with_unread = []
    for chat in chats:
         unread_count = ChatMessage.query.filter_by(
             chat_id=chat.id, 
             is_read=False,
             receiver_id=current_user.id # Only count messages sent TO the student
         ).count()
         # Add unread_count as a temporary attribute to the chat object
         chat.unread_count = unread_count 
         chats_with_unread.append(chat)
    # ------------------------------------------------------

    # Get active chat if chat_id is provided
    chat_id = request.args.get('chat_id', type=int)
    if chat_id:
        active_chat_query = Chat.query.filter(Chat.id == chat_id, Chat.student_id == current_user.id)
        active_chat = active_chat_query.first() # Use first() instead of get_or_404 to handle case where chat exists but isn't for this student

        if not active_chat:
             flash('Chat not found or access denied.', 'error')
             return redirect(url_for('chat_routes.chat_interface'))

        # --- Mark messages as read when chat is opened ---
        ChatMessage.query.filter_by(
            chat_id=active_chat.id, 
            receiver_id=current_user.id, 
            is_read=False
        ).update({ChatMessage.is_read: True})
        db.session.commit()
        # Re-fetch the active chat's unread count (should be 0 now)
        active_chat.unread_count = 0 
        # Also update the specific chat in the list
        for c in chats_with_unread:
            if c.id == active_chat.id:
                c.unread_count = 0
                break
        # ---------------------------------------------------

    # Render student chat template
    return render_template('chat/student_chat.html',
                            form=form,
                            chats=chats_with_unread, # Pass the list with counts
                            active_chat=active_chat)


@bp.route('/start/<int:teacher_id>')
@login_required
@role_required('student') # Ensure only students can use this
def start_or_get_chat(teacher_id):
    teacher = User.query.filter_by(id=teacher_id, role='teacher').first()
    if not teacher:
        flash('Teacher not found.', 'error')
        return redirect(request.referrer or url_for('student_routes.student_classes')) # Go back or to classes page

    # Check if chat already exists
    chat = Chat.query.filter_by(
        student_id=current_user.id,
        teacher_id=teacher.id
    ).first()

    if not chat:
        # Create a new chat
        chat = Chat(student_id=current_user.id, teacher_id=teacher.id)
        db.session.add(chat)
        db.session.commit()
        flash(f'Started chat with {teacher.username}.', 'success')

    # Redirect to the chat interface with the correct chat_id
    return redirect(url_for('chat_routes.chat_interface', chat_id=chat.id))

# --- Keep send_message and get_unread_count routes ---
# Modify send_message to set receiver_id correctly
@bp.route('/<int:chat_id>/send', methods=['POST'])
@login_required
def send_message(chat_id):
    chat = Chat.query.get_or_404(chat_id)

    # Determine receiver_id based on who the sender is
    if current_user.id == chat.student_id:
        receiver_id = chat.teacher_id
    elif current_user.id == chat.teacher_id:
         receiver_id = chat.student_id
    else:
         return jsonify({'status': 'error', 'message': 'Access denied'}), 403

    # Check if current user is part of this chat (redundant with above but good practice)
    if current_user.id not in [chat.teacher_id, chat.student_id]:
        return jsonify({'status': 'error', 'message': 'Access denied'}), 403

    # --- Using request directly instead of form for flexibility with JS FormData ---
    message_content = request.form.get('message')
    attachment_file = request.files.get('attachment')

    if not message_content and not attachment_file:
         return jsonify({'status': 'error', 'message': 'Cannot send empty message'}), 400

    # --- Create message object ---
    message = ChatMessage(
        chat_id=chat.id,
        sender_id=current_user.id,
        receiver_id=receiver_id, # Set the receiver
        content=message_content if message_content else "" # Handle case where only file is sent
    )

    # --- Handle file upload ---
    if attachment_file:
        # Add file type validation here if needed
        # Example: allowed_extensions = {'pdf', 'png', 'jpg', 'jpeg', 'docx', 'pptx'}
        # if '.' in attachment_file.filename and \
        #    attachment_file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:

        # Generate a unique filename (consider using UUIDs)
        filename = secure_filename(f"{chat.id}_{current_user.id}_{datetime.utcnow().timestamp()}_{attachment_file.filename}")
        # Save relative path for URL generation, store in static/uploads/...
        relative_folder = os.path.join('uploads', 'chat_attachments')
        absolute_folder = os.path.join(current_app.static_folder, relative_folder)
        os.makedirs(absolute_folder, exist_ok=True)

        full_path = os.path.join(absolute_folder, filename)
        attachment_file.save(full_path)
        message.attachment_path = os.path.join(relative_folder, filename).replace('\\', '/') # Store relative path with forward slashes
        # else:
        #    return jsonify({'status': 'error', 'message': 'Invalid file type'}), 400

    db.session.add(message)
    db.session.commit()

    # --- Emit new message event ---
    # Create sender/receiver specific room names
    sender_room = f'user_{message.sender_id}'
    receiver_room = f'user_{message.receiver_id}'

    message_data = {
        'chat_id': chat.id,
        'id': message.id, # Send message ID
        'content': message.content,
        'sender_id': message.sender_id,
        'sender_username': message.sender.username, # Send username
        'receiver_id': message.receiver_id,
        'created_at': message.created_at.isoformat() + "Z", # ISO format with Z for UTC
        'attachment_path': message.attachment_path,
        # Generate URL for attachment if it exists
        'attachment_url': url_for('static', filename=message.attachment_path, _external=True) if message.attachment_path else None
    }

    # Emit to both sender and receiver specifically (requires joining rooms on connect)
    socketio.emit('new_message', message_data, room=sender_room) 
    socketio.emit('new_message', message_data, room=receiver_room)

    # Return success response to the sender's fetch request
    return jsonify({
        'status': 'success',
        'message': message_data # Return the same data structure
    })

@bp.route('/unread_count')
@login_required
def get_unread_count():
    # Count messages where the current user is the receiver and is_read is False
    total_unread = ChatMessage.query.filter_by(
        receiver_id=current_user.id,
        is_read=False
    ).count()
    return jsonify({'unread_count': total_unread})

# --- SocketIO Events ---
@socketio.on('connect')
@login_required # Ensure user is logged in to connect
def handle_connect():
    # Join a room specific to the user
    user_room = f'user_{current_user.id}'
    join_room(user_room)
    print(f'User {current_user.username} connected and joined room {user_room}')

@socketio.on('disconnect')
def handle_disconnect():
    # Leave room (optional, SocketIO handles cleanup)
    if current_user.is_authenticated:
         user_room = f'user_{current_user.id}'
         leave_room(user_room)
         print(f'User {current_user.username} disconnected and left room {user_room}')
    else:
         print('Anonymous user disconnected')

# Add event handler for marking messages read via socket? (Alternative to route logic)
@socketio.on('mark_read')
@login_required
def handle_mark_read(data):
     chat_id = data.get('chat_id')
     if not chat_id:
         return 

     # Optional: Verify user is part of this chat
     chat = Chat.query.get(chat_id)
     if chat and current_user.id in [chat.student_id, chat.teacher_id]:
          updated_count = ChatMessage.query.filter_by(
               chat_id=chat_id, 
               receiver_id=current_user.id, 
               is_read=False
          ).update({ChatMessage.is_read: True})

          if updated_count > 0:
              db.session.commit()
              print(f"Marked {updated_count} messages as read in chat {chat_id} for user {current_user.id}")
              # Optionally emit an update back if needed
     else:
          print(f"User {current_user.id} attempted to mark read for invalid chat {chat_id}")