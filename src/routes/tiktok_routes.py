# Add these imports at the top of app_multiuser.py
from auth.multi_platform_oauth import multi_platform_oauth
from auth.tiktok.api_client import TikTokAPIClient

# Add these routes after the existing auth routes

@app.route('/api/auth/platforms')
def get_auth_platforms():
    """Get available authentication platforms and their status"""
    user = get_current_user()
    
    platforms = multi_platform_oauth.get_available_platforms()
    
    if user:
        # Get user's connected platforms
        connections = multi_platform_oauth.get_platform_connections(user)
        
        return jsonify({
            'available': platforms,
            'connected': connections
        })
    else:
        return jsonify({
            'available': platforms,
            'connected': {}
        })


@app.route('/api/auth/connect/<platform>')
@login_required
def connect_platform(platform):
    """Initiate connection to additional platform"""
    user = get_current_user()
    
    if platform not in ['tiktok']:
        return jsonify({'error': 'Invalid platform'}), 400
    
    redirect_uri = url_for('platform_callback', platform=platform, _external=True)
    
    auth_url, state = multi_platform_oauth.initiate_platform_auth(
        platform, redirect_uri, user
    )
    
    if not auth_url:
        return jsonify({'error': f'{platform} authentication not configured'}), 500
    
    # Store state for verification
    session[f'{platform}_oauth_state'] = state
    
    return jsonify({
        'authorization_url': auth_url,
        'status': 'redirect_required'
    })


@app.route('/api/auth/callback/<platform>')
def platform_callback(platform):
    """Handle OAuth callback for additional platforms"""
    # Verify state
    state = request.args.get('state')
    stored_state = session.pop(f'{platform}_oauth_state', None)
    
    if not state or state != stored_state:
        return render_template('auth_error.html', error='Invalid state parameter')
    
    redirect_uri = url_for('platform_callback', platform=platform, _external=True)
    
    user = multi_platform_oauth.handle_platform_callback(
        platform, request.url, state, redirect_uri
    )
    
    if user:
        # Redirect to main app with success message
        return redirect(url_for('index') + f'?platform_connected={platform}')
    else:
        return render_template('auth_error.html', error=f'{platform.title()} connection failed')


@app.route('/api/auth/disconnect/<platform>', methods=['POST'])
@login_required
def disconnect_platform(platform):
    """Disconnect a platform from user account"""
    user = get_current_user()
    
    if platform == 'google':
        return jsonify({'error': 'Cannot disconnect primary authentication'}), 400
    
    success = multi_platform_oauth.disconnect_platform(user, platform)
    
    if success:
        return jsonify({'status': 'success', 'message': f'{platform.title()} disconnected'})
    else:
        return jsonify({'error': 'Failed to disconnect platform'}), 500


@app.route('/api/upload_to_tiktok', methods=['POST'])
@login_required
def upload_to_tiktok():
    """Upload clip to TikTok"""
    user = get_current_user()
    
    # Get TikTok client
    tiktok_client = multi_platform_oauth.get_tiktok_client(user)
    if not tiktok_client:
        return jsonify({'error': 'TikTok not connected. Please connect your TikTok account first.'}), 401
    
    data = request.json
    job_id = data.get('job_id')
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    privacy_level = data.get('privacy_level', 'SELF_ONLY')
    allow_comments = data.get('allow_comments', True)
    allow_duet = data.get('allow_duet', True)
    allow_stitch = data.get('allow_stitch', True)
    upload_mode = data.get('upload_mode', 'draft')  # 'direct' or 'draft'
    
    if job_id not in active_jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = active_jobs[job_id]
    
    # Check authorization
    if job.user_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    if not job.clip_data:
        return jsonify({'error': 'No clip available for upload'}), 400
    
    if not title:
        return jsonify({'error': 'Title is required for TikTok'}), 400
    
    try:
        video_path = job.clip_data['path']
        
        if not os.path.exists(video_path):
            return jsonify({'error': 'Video file not found'}), 404
        
        # Create upload job ID
        upload_job_id = str(uuid.uuid4())
        
        # Start upload in background
        thread = threading.Thread(
            target=process_tiktok_upload,
            args=(user.id, tiktok_client, video_path, title, description,
                  privacy_level, allow_comments, allow_duet, allow_stitch,
                  upload_mode == 'direct', upload_job_id, job_id)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'started',
            'upload_job_id': upload_job_id,
            'message': 'TikTok upload started'
        })
        
    except Exception as e:
        logger.error(f"TikTok upload error: {e}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


def process_tiktok_upload(user_id, tiktok_client, video_path, title, description,
                         privacy_level, allow_comments, allow_duet, allow_stitch,
                         direct_post, upload_job_id, job_id):
    """Background process for TikTok upload"""
    try:
        # Progress callback
        def progress_callback(progress, message):
            socketio.emit('tiktok_upload_progress', {
                'upload_job_id': upload_job_id,
                'progress': progress,
                'message': message
            }, room=f"user_{user_id}")
        
        # Upload video
        result = tiktok_client.upload_video(
            video_path=video_path,
            title=title,
            description=description,
            privacy_level=privacy_level,
            allow_comments=allow_comments,
            allow_duet=allow_duet,
            allow_stitch=allow_stitch,
            direct_post=direct_post,
            progress_callback=progress_callback
        )
        
        if result:
            # Save to upload history
            conn = get_db_connection()
            cur = conn.cursor()
            
            try:
                cur.execute('''
                    INSERT INTO tiktok_upload_history 
                    (user_id, job_id, publish_id, video_title, video_description,
                     video_path, share_url, privacy_level, upload_type, upload_status, completed_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ''', (
                    user_id, job_id, result.get('publish_id'),
                    title, description, video_path,
                    result.get('share_url'), privacy_level,
                    'direct' if direct_post else 'draft',
                    'completed'
                ))
                conn.commit()
            finally:
                cur.close()
                conn.close()
            
            # Emit success
            socketio.emit('tiktok_upload_complete', {
                'upload_job_id': upload_job_id,
                'status': 'success',
                'share_url': result.get('share_url'),
                'message': 'Successfully uploaded to TikTok!'
            }, room=f"user_{user_id}")
            
        else:
            # Emit failure
            socketio.emit('tiktok_upload_error', {
                'upload_job_id': upload_job_id,
                'status': 'failed',
                'error': 'Upload failed'
            }, room=f"user_{user_id}")
            
    except Exception as e:
        logger.error(f"TikTok upload process error: {e}")
        
        # Emit error
        socketio.emit('tiktok_upload_error', {
            'upload_job_id': upload_job_id,
            'status': 'failed',
            'error': str(e)
        }, room=f"user_{user_id}")


@app.route('/api/tiktok/upload_history')
@login_required
def get_tiktok_history():
    """Get user's TikTok upload history"""
    user = get_current_user()
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute('''
            SELECT * FROM tiktok_upload_history 
            WHERE user_id = %s 
            ORDER BY uploaded_at DESC 
            LIMIT 20
        ''', (user.id,))
        
        history = cur.fetchall()
        
        return jsonify({
            'uploads': [
                {
                    'publish_id': item['publish_id'],
                    'title': item['video_title'],
                    'description': item['video_description'],
                    'share_url': item['share_url'],
                    'privacy_level': item['privacy_level'],
                    'upload_type': item['upload_type'],
                    'status': item['upload_status'],
                    'uploaded_at': item['uploaded_at'].isoformat() if item['uploaded_at'] else None,
                    'completed_at': item['completed_at'].isoformat() if item['completed_at'] else None
                }
                for item in history
            ]
        })
    finally:
        cur.close()
        conn.close()
