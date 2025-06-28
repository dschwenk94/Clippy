// 🎬 Clippy - Edit Page JavaScript

class EditPage {
    constructor() {
        this.jobId = document.getElementById('job-id').value;
        this.clipData = JSON.parse(document.getElementById('clip-data').value || '{}');
        this.socket = null;
        this.hasUnsavedChanges = false;
        
        // Caption settings
        this.captionPosition = 'bottom';
        this.speakerColors = {
            1: '#FF4500', // Red
            2: '#00BFFF', // Blue  
            3: '#00FF88'  // Green
        };
        
        // New speaker styling settings
        this.speakerSettings = {
            1: {
                font: 'Impact',
                fillColor: '#FF4500',
                outlineColor: '#000000',
                outlineThickness: 2
            },
            2: {
                font: 'Impact',
                fillColor: '#00BFFF',
                outlineColor: '#000000',
                outlineThickness: 2
            },
            3: {
                font: 'Impact',
                fillColor: '#00FF88',
                outlineColor: '#000000',
                outlineThickness: 2
            }
        };
        
        // Current active speaker tab
        this.activeSpeaker = 1;
        
        // Color picker state
        this.colorPickerTarget = null;
        
        // End Screen settings
        this.endScreenEnabled = false;
        this.endScreenText = 'SUBSCRIBE';
        this.endScreenDuration = 3.0;
        this.endScreenPosition = 'middle';
        this.endScreenColor = '#FF4500';
        
        console.log('EditPage initialized with:', {
            jobId: this.jobId,
            clipData: this.clipData
        });
        
        if (!this.jobId) {
            window.location.href = '/';
            return;
        }
        
        // Debug: Check job status
        this.debugJob();
        
        this.initializeSocket();
        this.loadVideo();
        this.loadCaptions();
        this.initializeEventListeners();
        this.initializeColorPreviews();
    }

    initializeSocket() {
        this.socket = io({
            query: {
                job_id: this.jobId
            }
        });

        this.socket.on('connect', () => {
            console.log('Connected to server');
        });

        this.socket.on('regeneration_update', (data) => {
            if (data.job_id === this.jobId) {
                this.handleRegenerationUpdate(data);
            }
        });

        this.socket.on('regeneration_complete', (data) => {
            if (data.job_id === this.jobId) {
                this.handleRegenerationComplete(data);
            }
        });

        this.socket.on('regeneration_error', (data) => {
            if (data.job_id === this.jobId) {
                this.handleRegenerationError(data);
            }
        });
    }

    loadVideo() {
        const video = document.getElementById('clip-video');
        const videoSource = document.getElementById('video-source');
        
        console.log('Loading video, clipData:', this.clipData);
        
        // Try different path formats
        let videoPath = null;
        
        if (this.clipData.path) {
            videoPath = this.clipData.path;
        } else if (this.clipData.video_path) {
            videoPath = this.clipData.video_path;
        } else if (this.clipData.clip_path) {
            videoPath = this.clipData.clip_path;
        }
        
        if (videoPath) {
            // Extract just the filename
            const filename = videoPath.split('/').pop();
            const videoUrl = `/clips/${filename}`;
            console.log('Setting video source to:', videoUrl);
            videoSource.src = videoUrl;
            video.load();
            
            // Add error handler
            video.addEventListener('error', (e) => {
                console.error('Video load error:', e);
                console.error('Video error details:', video.error);
                // Try fallback: look for the video without path
                this.tryFallbackVideo();
            });
            
            video.addEventListener('loadeddata', () => {
                console.log('Video loaded successfully');
            });
        } else {
            console.warn('No video path found in clipData');
            // Try to find a video based on job ID or other info
            this.tryFallbackVideo();
        }

        // Load clip details
        this.displayClipDetails();
    }
    
    tryFallbackVideo() {
        console.log('Trying fallback video loading...');
        // If we have any clip info, try to construct a path
        const video = document.getElementById('clip-video');
        const videoSource = document.getElementById('video-source');
        
        // Common patterns for video files
        // First, try to get a list of available clips
        this.getAvailableClips().then(clips => {
            if (clips && clips.length > 0) {
                // Try the most recent clip first
                const mostRecent = clips[clips.length - 1];
                console.log('Trying most recent clip:', mostRecent);
                
                videoSource.src = `/clips/${mostRecent}`;
                video.load();
                
                video.onloadeddata = () => {
                    console.log('Loaded most recent clip:', mostRecent);
                };
                
                video.onerror = () => {
                    console.error('Failed to load most recent clip');
                };
            }
        });
        
        const possiblePatterns = [
            `auto_peak_clip_${this.clipData.video_id}_${this.clipData.optimal_timestamp}s.mp4`,
            `auto_peak_clip__${this.clipData.optimal_timestamp}s.mp4`,
            `clip_${this.jobId}.mp4`
        ];
        
        let attemptIndex = 0;
        
        const tryNextPattern = () => {
            if (attemptIndex >= possiblePatterns.length) {
                console.error('All fallback patterns failed');
                return;
            }
            
            const testUrl = `/clips/${possiblePatterns[attemptIndex]}`;
            console.log('Trying fallback URL:', testUrl);
            
            videoSource.src = testUrl;
            video.load();
            
            video.onerror = () => {
                attemptIndex++;
                tryNextPattern();
            };
            
            video.onloadeddata = () => {
                console.log('Fallback video loaded successfully:', testUrl);
            };
        };
        
        tryNextPattern();
    }

    async getAvailableClips() {
        try {
            const response = await fetch('/api/available_clips');
            if (response.ok) {
                const data = await response.json();
                return data.clips || [];
            }
        } catch (error) {
            console.error('Error getting available clips:', error);
        }
        return [];
    }
    
    displayClipDetails() {
        const detailsContainer = document.getElementById('clip-details');
        
        const startTime = this.clipData.optimal_timestamp || 0;
        const endTime = startTime + (this.clipData.duration || 30);
        const startMMSS = window.clippyBase.formatSecondsToMMSS(startTime);
        const endMMSS = window.clippyBase.formatSecondsToMMSS(endTime);
        
        detailsContainer.innerHTML = `
            <div class="info-item">
                <div class="info-label">Timing</div>
                <div class="info-value">${startMMSS} - ${endMMSS}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Duration</div>
                <div class="info-value">${this.clipData.duration || 30}s</div>
            </div>
            <div class="info-item">
                <div class="info-label">Detection</div>
                <div class="info-value">${this.clipData.auto_detected ? 'AI Auto' : 'Manual'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Confidence</div>
                <div class="info-value">${(this.clipData.detection_confidence || 0).toFixed(2)}</div>
            </div>
        `;
    }

    loadCaptions() {
        const captionsEditor = document.getElementById('captions-editor');
        let captions = this.clipData.captions || [];
        
        console.log('Loading captions:', captions);
        
        // If no captions but we have a subtitle file, try to load them
        if (captions.length === 0 && this.clipData.subtitle_file) {
            console.log('No captions in data, but subtitle file exists:', this.clipData.subtitle_file);
            // In a real implementation, we'd fetch and parse the subtitle file
            // For now, we'll just show a message
            captionsEditor.innerHTML = `
                <div class="no-captions">
                    <p>Captions file exists but not loaded</p>
                    <p class="caption-file-info">File: ${this.clipData.subtitle_file}</p>
                    <button class="btn btn-sm btn-secondary" onclick="window.editPage.reloadCaptions()">Reload Captions</button>
                </div>
            `;
            return;
        }
        
        if (captions.length === 0) {
            captionsEditor.innerHTML = '<p class="no-captions">No captions available</p>';
            return;
        }

        let html = '';
        captions.forEach((caption, index) => {
            const speakerNum = this.getSpeakerNumber(caption.speaker);
            const speakerClass = `speaker-${speakerNum}`;
            const speakerColor = this.speakerColors[speakerNum];
            
            html += `
                <div class="caption-item" data-index="${index}">
                    <div class="caption-header">
                        <select class="speaker-selector ${speakerClass}" data-index="${index}" 
                                style="border-color: ${speakerColor}; color: ${speakerColor}">
                            <option value="1" ${speakerNum === 1 ? 'selected' : ''}>Speaker 1</option>
                            <option value="2" ${speakerNum === 2 ? 'selected' : ''}>Speaker 2</option>
                            <option value="3" ${speakerNum === 3 ? 'selected' : ''}>Speaker 3</option>
                        </select>
                        <span class="caption-time">${caption.start_time} → ${caption.end_time}</span>
                    </div>
                    <textarea class="caption-text-input" 
                             data-index="${index}" 
                             placeholder="Edit caption text..."
                             rows="2">${caption.text}</textarea>
                </div>
            `;
        });

        captionsEditor.innerHTML = html;
        
        // Add event listeners to new elements
        this.attachCaptionListeners();
    }

    attachCaptionListeners() {
        // Speaker selectors
        document.querySelectorAll('.speaker-selector').forEach(select => {
            select.addEventListener('change', (e) => {
                this.handleSpeakerChange(e);
                this.hasUnsavedChanges = true;
            });
        });
        
        // Text inputs
        document.querySelectorAll('.caption-text-input').forEach(textarea => {
            textarea.addEventListener('input', (e) => {
                this.hasUnsavedChanges = true;
                // Auto-resize
                e.target.style.height = 'auto';
                e.target.style.height = e.target.scrollHeight + 'px';
            });
            
            // Initial resize
            textarea.style.height = 'auto';
            textarea.style.height = textarea.scrollHeight + 'px';
        });
    }

    initializeColorPreviews() {
        // Update preview with current speaker settings
        this.updateCaptionPreview();
    }
    
    initializeCaptionStylingControls() {
        // Speaker tabs
        document.querySelectorAll('.speaker-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const speaker = parseInt(e.target.dataset.speaker);
                this.switchSpeakerTab(speaker);
            });
        });
        
        // Font selectors
        document.querySelectorAll('.font-select').forEach(select => {
            select.addEventListener('change', (e) => {
                const speaker = parseInt(e.target.dataset.speaker);
                this.speakerSettings[speaker].font = e.target.value;
                this.hasUnsavedChanges = true;
                if (speaker === this.activeSpeaker) {
                    this.updateCaptionPreview();
                }
            });
        });
        
        // Color picker buttons
        document.querySelectorAll('.color-picker-button').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const speaker = parseInt(button.dataset.speaker);
                const colorType = button.dataset.colorType;
                this.openColorPicker(speaker, colorType, button);
            });
        });
        
        // Outline thickness sliders
        document.querySelectorAll('.control-slider').forEach(slider => {
            slider.addEventListener('input', (e) => {
                const speaker = parseInt(e.target.dataset.speaker);
                const value = parseFloat(e.target.value);
                this.speakerSettings[speaker].outlineThickness = value;
                
                // Update value display
                const valueSpan = e.target.nextElementSibling;
                if (valueSpan) {
                    valueSpan.textContent = `${value}px`;
                }
                
                this.hasUnsavedChanges = true;
                if (speaker === this.activeSpeaker) {
                    this.updateCaptionPreview();
                }
            });
        });
        
        // Apply to all buttons
        document.querySelectorAll('.apply-all-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const sourceSpeaker = parseInt(e.target.dataset.speaker);
                this.applySettingsToAllSpeakers(sourceSpeaker);
            });
        });
        
        // Initialize color picker
        this.initializeColorPicker();
    }
    
    switchSpeakerTab(speaker) {
        this.activeSpeaker = speaker;
        
        // Update tab styles
        document.querySelectorAll('.speaker-tab').forEach(tab => {
            tab.classList.toggle('active', parseInt(tab.dataset.speaker) === speaker);
        });
        
        // Show/hide panels
        document.querySelectorAll('.speaker-settings-panel').forEach(panel => {
            panel.classList.toggle('active', parseInt(panel.dataset.speaker) === speaker);
        });
        
        // Update preview
        this.updateCaptionPreview();
    }
    
    updateCaptionPreview() {
        const preview = document.getElementById('caption-preview');
        if (!preview) return;
        
        const settings = this.speakerSettings[this.activeSpeaker];
        const previewText = preview.querySelector('.preview-text');
        
        if (previewText) {
            previewText.style.fontFamily = settings.font;
            previewText.style.color = settings.fillColor;
            previewText.style.webkitTextStroke = `${settings.outlineThickness}px ${settings.outlineColor}`;
            previewText.style.textStroke = `${settings.outlineThickness}px ${settings.outlineColor}`;
            previewText.style.paintOrder = 'stroke fill';
        }
    }
    
    initializeColorPicker() {
        const popup = document.getElementById('color-picker-popup');
        const closeBtn = popup.querySelector('.color-picker-close');
        const applyBtn = document.getElementById('color-picker-apply');
        const colorInput = document.getElementById('color-input');
        const canvas = document.getElementById('color-wheel');
        const ctx = canvas.getContext('2d');
        
        // Close button
        closeBtn.addEventListener('click', () => {
            this.closeColorPicker();
        });
        
        // Apply button
        applyBtn.addEventListener('click', () => {
            this.applyColorFromPicker();
        });
        
        // Color input
        colorInput.addEventListener('input', (e) => {
            this.updateColorPreview(e.target.value);
        });
        
        // Draw color wheel
        this.drawColorWheel(ctx, canvas.width, canvas.height);
        
        // Canvas click
        canvas.addEventListener('click', (e) => {
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const color = this.getColorFromWheel(ctx, x, y);
            if (color) {
                colorInput.value = color;
                this.updateColorPreview(color);
            }
        });
        
        // Close on outside click
        popup.addEventListener('click', (e) => {
            if (e.target === popup) {
                this.closeColorPicker();
            }
        });
    }
    
    drawColorWheel(ctx, width, height) {
        const centerX = width / 2;
        const centerY = height / 2;
        const radius = Math.min(width, height) / 2 - 5;
        
        // Create color wheel using HSL
        for (let angle = 0; angle < 360; angle += 1) {
            const startAngle = (angle - 1) * Math.PI / 180;
            const endAngle = angle * Math.PI / 180;
            
            for (let r = 0; r < radius; r++) {
                const saturation = (r / radius) * 100;
                const lightness = 50;
                
                ctx.beginPath();
                ctx.arc(centerX, centerY, r, startAngle, endAngle);
                ctx.strokeStyle = `hsl(${angle}, ${saturation}%, ${lightness}%)`;
                ctx.lineWidth = 2;
                ctx.stroke();
            }
        }
    }
    
    getColorFromWheel(ctx, x, y) {
        const imageData = ctx.getImageData(x, y, 1, 1);
        const data = imageData.data;
        
        if (data[3] > 0) { // Check alpha
            const r = data[0];
            const g = data[1];
            const b = data[2];
            return this.rgbToHex(r, g, b);
        }
        return null;
    }
    
    rgbToHex(r, g, b) {
        return '#' + [r, g, b].map(x => {
            const hex = x.toString(16);
            return hex.length === 1 ? '0' + hex : hex;
        }).join('');
    }
    
    openColorPicker(speaker, colorType, button) {
        const popup = document.getElementById('color-picker-popup');
        const colorInput = document.getElementById('color-input');
        
        // Store current target
        this.colorPickerTarget = { speaker, colorType, button };
        
        // Set current color
        const currentColor = colorType === 'fill' 
            ? this.speakerSettings[speaker].fillColor 
            : this.speakerSettings[speaker].outlineColor;
        
        colorInput.value = currentColor;
        this.updateColorPreview(currentColor);
        
        // Position popup near button
        const rect = button.getBoundingClientRect();
        popup.style.left = `${rect.left}px`;
        popup.style.top = `${rect.bottom + 10}px`;
        
        // Show popup
        popup.classList.remove('hidden');
    }
    
    closeColorPicker() {
        const popup = document.getElementById('color-picker-popup');
        popup.classList.add('hidden');
        this.colorPickerTarget = null;
    }
    
    updateColorPreview(color) {
        const preview = document.getElementById('color-preview');
        if (preview) {
            preview.style.backgroundColor = color;
        }
    }
    
    applyColorFromPicker() {
        if (!this.colorPickerTarget) return;
        
        const { speaker, colorType, button } = this.colorPickerTarget;
        const color = document.getElementById('color-input').value;
        
        // Update settings
        if (colorType === 'fill') {
            this.speakerSettings[speaker].fillColor = color;
            // Also update the old speakerColors for backward compatibility
            this.speakerColors[speaker] = color;
        } else {
            this.speakerSettings[speaker].outlineColor = color;
        }
        
        // Update button
        button.style.backgroundColor = color;
        button.querySelector('.color-value').textContent = color;
        
        // Update preview if current speaker
        if (speaker === this.activeSpeaker) {
            this.updateCaptionPreview();
        }
        
        // Update speaker tab color if fill color
        if (colorType === 'fill') {
            const tab = document.querySelector(`.speaker-tab[data-speaker="${speaker}"]`);
            if (tab) {
                tab.style.setProperty('--tab-color', color);
            }
        }
        
        this.hasUnsavedChanges = true;
        this.closeColorPicker();
    }
    
    applySettingsToAllSpeakers(sourceSpeaker) {
        const sourceSettings = this.speakerSettings[sourceSpeaker];
        
        // Copy settings to all speakers
        for (let speaker = 1; speaker <= 3; speaker++) {
            if (speaker !== sourceSpeaker) {
                // Keep the original fill color but copy other settings
                const originalFillColor = this.speakerSettings[speaker].fillColor;
                this.speakerSettings[speaker] = {
                    ...sourceSettings,
                    fillColor: originalFillColor
                };
                
                // Update UI for this speaker
                const fontSelect = document.getElementById(`speaker-${speaker}-font`);
                if (fontSelect) fontSelect.value = sourceSettings.font;
                
                const outlineColorBtn = document.querySelector(`.color-picker-button[data-speaker="${speaker}"][data-color-type="outline"]`);
                if (outlineColorBtn) {
                    outlineColorBtn.style.backgroundColor = sourceSettings.outlineColor;
                    outlineColorBtn.querySelector('.color-value').textContent = sourceSettings.outlineColor;
                }
                
                const thicknessSlider = document.getElementById(`speaker-${speaker}-outline-thickness`);
                if (thicknessSlider) {
                    thicknessSlider.value = sourceSettings.outlineThickness;
                    const valueSpan = thicknessSlider.nextElementSibling;
                    if (valueSpan) valueSpan.textContent = `${sourceSettings.outlineThickness}px`;
                }
            }
        }
        
        this.hasUnsavedChanges = true;
        window.clippyBase.showSuccess('Settings applied to all speakers!');
    }
    
    initializeEventListeners() {
        // Toggle captions button
        document.getElementById('toggle-captions')?.addEventListener('click', () => {
            this.toggleCaptions();
        });

        // Update captions button
        document.getElementById('update-captions-btn').addEventListener('click', () => {
            this.updateCaptions();
        });

        // Continue button
        document.getElementById('continue-btn').addEventListener('click', () => {
            this.continueToUpload();
        });
        
        // Caption position selector
        document.getElementById('caption-position')?.addEventListener('change', (e) => {
            this.captionPosition = e.target.value;
            this.hasUnsavedChanges = true;
        });
        
        // Initialize new caption styling controls
        this.initializeCaptionStylingControls();
        
        // End Screen controls
        this.initializeEndScreenControls();
        
        // Warn about unsaved changes
        window.addEventListener('beforeunload', (e) => {
            if (this.hasUnsavedChanges) {
                e.preventDefault();
                e.returnValue = '';
            }
        });
    }
    
    initializeEndScreenControls() {
        const enableCheckbox = document.getElementById('end-screen-enabled');
        const settingsDiv = document.getElementById('end-screen-settings');
        const durationSlider = document.getElementById('end-screen-duration');
        const durationValue = document.getElementById('duration-value');
        const textArea = document.getElementById('end-screen-text');
        const positionSelect = document.getElementById('end-screen-position');
        const colorSelect = document.getElementById('end-screen-color');
        
        // Enable/disable toggle
        enableCheckbox?.addEventListener('change', (e) => {
            this.endScreenEnabled = e.target.checked;
            settingsDiv.classList.toggle('hidden', !this.endScreenEnabled);
            this.hasUnsavedChanges = true;
        });
        
        // Duration slider
        durationSlider?.addEventListener('input', (e) => {
            this.endScreenDuration = parseFloat(e.target.value);
            durationValue.textContent = `${this.endScreenDuration.toFixed(1)}s`;
            this.hasUnsavedChanges = true;
        });
        
        // Text input
        textArea?.addEventListener('input', (e) => {
            this.endScreenText = e.target.value;
            this.hasUnsavedChanges = true;
        });
        
        // Position select
        positionSelect?.addEventListener('change', (e) => {
            this.endScreenPosition = e.target.value;
            this.hasUnsavedChanges = true;
        });
        
        // Color select
        colorSelect?.addEventListener('change', (e) => {
            this.endScreenColor = e.target.value;
            // Update color preview
            colorSelect.setAttribute('value', e.target.value);
            this.hasUnsavedChanges = true;
        });
        
        // Initialize color preview
        colorSelect?.setAttribute('value', this.endScreenColor);
    }

    getSpeakerNumber(speakerName) {
        if (!speakerName) return 1;
        const match = speakerName.match(/(\d+)/);
        return match ? parseInt(match[1]) : 1;
    }

    handleSpeakerChange(event) {
        const select = event.target;
        const newSpeakerNum = parseInt(select.value);
        
        // Update visual style with custom color
        const color = this.speakerColors[newSpeakerNum];
        select.className = `speaker-selector speaker-${newSpeakerNum}`;
        select.style.borderColor = color;
        select.style.color = color;
    }
    
    updateSpeakerColor(speaker, color) {
        this.speakerColors[speaker] = color;
        
        // Update all speaker selectors with this speaker number
        document.querySelectorAll(`.speaker-selector`).forEach(select => {
            if (parseInt(select.value) === speaker) {
                select.style.borderColor = color;
                select.style.color = color;
            }
        });
        
        // Update the visual preview of the color dropdown
        const colorSelect = document.querySelector(`#speaker-${speaker}-color`);
        if (colorSelect) {
            colorSelect.style.borderColor = color;
            // Update the color dot by changing the select value attribute for CSS
            colorSelect.setAttribute('value', color);
        }
    }

    toggleCaptions() {
        // This would toggle caption display on the video
        // Implementation depends on how captions are rendered
        const video = document.getElementById('clip-video');
        const track = video.querySelector('track');
        
        if (track) {
            track.mode = track.mode === 'showing' ? 'hidden' : 'showing';
        }
    }

    async updateCaptions() {
        if (!this.hasUnsavedChanges) {
            window.clippyBase.showError('No changes to update');
            return;
        }

        // Collect updated captions
        const captionItems = document.querySelectorAll('.caption-item');
        const updatedCaptions = Array.from(captionItems).map(item => {
            const index = parseInt(item.dataset.index);
            const textInput = item.querySelector('.caption-text-input');
            const speakerSelect = item.querySelector('.speaker-selector');
            
            return {
                index: index,
                text: textInput.value,
                speaker: `Speaker ${speakerSelect.value}`
            };
        });

        // Show update progress
        this.showUpdateProgress();

        try {
            const response = await fetch('/api/update_captions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    job_id: this.jobId,
                    captions: updatedCaptions,
                    caption_position: this.captionPosition,
                    speaker_colors: this.speakerColors,
                    speaker_settings: this.speakerSettings,  // Add new speaker settings
                    end_screen: {
                        enabled: this.endScreenEnabled,
                        text: this.endScreenText,
                        duration: this.endScreenDuration,
                        position: this.endScreenPosition,
                        color: this.endScreenColor
                    }
                })
            });

            const result = await response.json();

            if (response.ok) {
                this.hasUnsavedChanges = false;
                // Progress will be shown via socket events
            } else {
                this.hideUpdateProgress();
                window.clippyBase.showError(result.error || 'Failed to update captions');
            }
        } catch (error) {
            console.error('Update captions error:', error);
            this.hideUpdateProgress();
            window.clippyBase.showError('Network error occurred');
        }
    }

    showUpdateProgress() {
        const progressDiv = document.getElementById('update-progress');
        if (progressDiv) {
            progressDiv.classList.remove('hidden');
        }
    }

    hideUpdateProgress() {
        const progressDiv = document.getElementById('update-progress');
        if (progressDiv) {
            progressDiv.classList.add('hidden');
        }
    }

    handleRegenerationUpdate(data) {
        const progressFill = document.querySelector('.update-progress-fill');
        const progressText = document.querySelector('.update-text');
        
        if (progressFill) {
            progressFill.style.width = `${data.progress}%`;
        }
        
        if (progressText) {
            progressText.textContent = data.message;
        }
    }

    handleRegenerationComplete(data) {
        this.hideUpdateProgress();
        window.clippyBase.showSuccess('Video updated successfully!');
        
        // Refresh video
        this.refreshVideo();
    }

    handleRegenerationError(data) {
        this.hideUpdateProgress();
        window.clippyBase.showError(`Update failed: ${data.error}`);
    }

    async refreshVideo() {
        try {
            const response = await fetch(`/api/refresh_video/${this.jobId}`);
            const result = await response.json();
            
            if (response.ok) {
                // Update clip data
                this.clipData = result.clip_data;
                
                // Reload video with cache buster
                const video = document.getElementById('clip-video');
                const videoSource = document.getElementById('video-source');
                videoSource.src = result.video_url;
                video.load();
                
                // Reload captions
                if (result.captions) {
                    this.clipData.captions = result.captions;
                    this.loadCaptions();
                }
            }
        } catch (error) {
            console.error('Refresh video error:', error);
        }
    }

    continueToUpload() {
        // Check if user is authenticated
        if (!window.clippyBase.currentUser) {
            // Show auth prompt
            this.showAuthPrompt();
        } else {
            // Navigate to upload page
            window.location.href = `/upload?job_id=${this.jobId}`;
        }
    }

    showAuthPrompt() {
        const authPrompt = document.createElement('div');
        authPrompt.className = 'auth-prompt-overlay';
        authPrompt.innerHTML = `
            <div class="auth-prompt-modal">
                <h2>Sign in to Upload</h2>
                <p>To upload your clip to YouTube or TikTok, you need to sign in with your Google account.</p>
                
                <div class="auth-benefits">
                    <h4>Benefits of signing in:</h4>
                    <ul>
                        <li>
                            <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                            </svg>
                            Upload directly to YouTube and TikTok
                        </li>
                        <li>
                            <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                            </svg>
                            Track your upload history
                        </li>
                        <li>
                            <svg width="20" height="20" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                            </svg>
                            Save clips to your account
                        </li>
                    </ul>
                </div>
                
                <div class="auth-actions">
                    <button class="btn btn-primary btn-lg" id="auth-prompt-signin">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M19.6 10.227c0-.709-.064-1.39-.182-2.045H10v3.868h5.382a4.6 4.6 0 01-1.996 3.018v2.51h3.232c1.891-1.742 2.982-4.305 2.982-7.35z" fill="#4285F4"/>
                            <path d="M10 20c2.7 0 4.964-.895 6.618-2.423l-3.232-2.509c-.895.6-2.04.955-3.386.955-2.605 0-4.81-1.76-5.595-4.123H1.064v2.59A9.996 9.996 0 0010 20z" fill="#34A853"/>
                            <path d="M4.405 11.9c-.2-.6-.314-1.24-.314-1.9 0-.66.114-1.3.314-1.9V5.51H1.064A9.996 9.996 0 000 10c0 1.614.386 3.14 1.064 4.49l3.34-2.59z" fill="#FBBC05"/>
                            <path d="M10 3.977c1.468 0 2.786.505 3.823 1.496l2.868-2.868C14.959.992 12.695 0 10 0 6.09 0 2.71 2.24 1.064 5.51l3.34 2.59C5.192 5.736 7.396 3.977 10 3.977z" fill="#EA4335"/>
                        </svg>
                        Sign in with Google
                    </button>
                    <button class="btn btn-ghost" id="auth-prompt-cancel">
                        Continue Editing
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(authPrompt);
        
        // Add event listeners
        document.getElementById('auth-prompt-signin').addEventListener('click', () => {
            window.clippyBase.signInWithGoogle();
        });
        
        document.getElementById('auth-prompt-cancel').addEventListener('click', () => {
            authPrompt.remove();
        });
        
        // Close on background click
        authPrompt.addEventListener('click', (e) => {
            if (e.target === authPrompt) {
                authPrompt.remove();
            }
        });
    }
    
    async debugJob() {
        try {
            const response = await fetch(`/api/debug/job/${this.jobId}`);
            const data = await response.json();
            console.log('Job debug info:', data);
            
            // Log specific important fields
            if (data.clip_data_keys) {
                console.log('Clip data keys:', data.clip_data_keys);
            }
            if (data.files_info) {
                console.log('Files info:', data.files_info);
            }
            if (data.error) {
                console.error('Job error:', data.error);
            }
            
            // If no clip data, try to refresh
            if (!data.clip_data_keys || data.clip_data_keys.length === 0) {
                console.warn('No clip data found, attempting to fix...');
                
                // Check if we have reconstructed data
                if (data.reconstructed_data) {
                    console.log('Found reconstructed data:', data.reconstructed_data);
                    this.fixJobData();
                } else {
                    setTimeout(() => this.refreshVideoData(), 1000);
                }
            }
        } catch (error) {
            console.error('Debug job error:', error);
        }
    }
    
    async fixJobData() {
        console.log('Attempting to fix job data...');
        try {
            const response = await fetch(`/api/fix_job/${this.jobId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success && data.clip_data) {
                console.log('Job data fixed:', data.clip_data);
                this.clipData = data.clip_data;
                
                // Reload everything
                this.loadVideo();
                this.loadCaptions();
                this.displayClipDetails();
                
                window.clippyBase.showSuccess('Clip data recovered successfully');
            } else {
                console.error('Failed to fix job data:', data);
                window.clippyBase.showError('Could not recover clip data');
            }
        } catch (error) {
            console.error('Fix job data error:', error);
        }
    }
    
    async refreshVideoData() {
        try {
            const response = await fetch(`/api/refresh_video/${this.jobId}`);
            const data = await response.json();
            
            if (data.status === 'success' && data.clip_data) {
                console.log('Refreshed clip data:', data.clip_data);
                this.clipData = data.clip_data;
                
                // Reload video and captions
                this.loadVideo();
                this.loadCaptions();
            } else {
                console.error('Failed to refresh video data:', data);
            }
        } catch (error) {
            console.error('Refresh video data error:', error);
        }
    }
    
    async reloadCaptions() {
        console.log('Reloading captions...');
        try {
            const response = await fetch(`/api/refresh_video/${this.jobId}`);
            const data = await response.json();
            
            if (data.captions && data.captions.length > 0) {
                this.clipData.captions = data.captions;
                this.loadCaptions();
                window.clippyBase.showSuccess('Captions reloaded successfully');
            } else {
                window.clippyBase.showError('No captions found');
            }
        } catch (error) {
            console.error('Reload captions error:', error);
            window.clippyBase.showError('Failed to reload captions');
        }
    }
}

// Add edit page specific styles
const editPageStyles = `
<style>
/* Edit Page Specific Styles */
.edit-page {
    min-height: calc(100vh - 200px);
}

.edit-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-xl);
    max-width: 1400px;
    margin: 0 auto;
}

/* Video Panel */
.video-panel {
    background: var(--color-surface-elevated);
    border-radius: var(--radius-xl);
    padding: var(--space-lg);
}

.panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-lg);
}

.panel-header h2 {
    font-size: var(--text-xl);
    font-weight: 600;
}

.video-wrapper {
    position: relative;
    border-radius: var(--radius-lg);
    overflow: hidden;
    margin-bottom: var(--space-lg);
    background: black;
    aspect-ratio: 16/9;
}

.video-player {
    width: 100%;
    height: 100%;
    object-fit: contain;
}

/* Video Info Card */
.video-info-card {
    background: var(--color-surface-overlay);
    border-radius: var(--radius-lg);
    padding: var(--space-md);
}

.video-info-card h3 {
    font-size: var(--text-base);
    font-weight: 600;
    margin-bottom: var(--space-md);
}

.video-info-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-md);
}

.info-item {
    display: flex;
    flex-direction: column;
    gap: var(--space-xs);
}

.info-label {
    font-size: var(--text-xs);
    color: var(--color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.info-value {
    font-size: var(--text-base);
    font-weight: 500;
}

/* Caption Panel */
.caption-panel {
    background: var(--color-surface-elevated);
    border-radius: var(--radius-xl);
    padding: var(--space-lg);
    display: flex;
    flex-direction: column;
}

.panel-description {
    font-size: var(--text-sm);
    color: var(--color-text-secondary);
}

/* Caption Editor */
.caption-editor {
    flex: 1;
    overflow-y: auto;
    margin-bottom: var(--space-lg);
    padding-right: var(--space-sm);
    max-height: 500px;
}

.caption-editor::-webkit-scrollbar {
    width: 6px;
}

.caption-editor::-webkit-scrollbar-track {
    background: var(--color-surface);
    border-radius: 3px;
}

.caption-editor::-webkit-scrollbar-thumb {
    background: var(--color-border);
    border-radius: 3px;
}

.caption-editor::-webkit-scrollbar-thumb:hover {
    background: var(--color-primary);
}

/* Caption Item */
.caption-item {
    background: var(--color-surface-overlay);
    border-radius: var(--radius-lg);
    padding: var(--space-md);
    margin-bottom: var(--space-sm);
    transition: all var(--transition-base);
    border: 2px solid transparent;
}

.caption-item:hover {
    border-color: var(--color-border);
}

.caption-item:focus-within {
    border-color: var(--color-primary);
    background: var(--color-surface);
}

.caption-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-sm);
}

.speaker-selector {
    padding: var(--space-xs) var(--space-sm);
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    color: var(--color-text-primary);
    font-size: var(--text-sm);
    font-weight: 500;
    cursor: pointer;
    transition: all var(--transition-base);
}

.speaker-1 { border-color: #ef4444; color: #ef4444; }
.speaker-2 { border-color: #3b82f6; color: #3b82f6; }
.speaker-3 { border-color: #10b981; color: #10b981; }

.caption-time {
    font-size: var(--text-xs);
    color: var(--color-text-muted);
    font-family: var(--font-mono);
}

.caption-text-input {
    width: 100%;
    padding: var(--space-sm);
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    color: var(--color-text-primary);
    font-size: var(--text-base);
    line-height: 1.5;
    resize: none;
    transition: all var(--transition-base);
    font-family: inherit;
}

.caption-text-input:focus {
    outline: none;
    border-color: var(--color-primary);
    background: var(--color-surface-elevated);
}

.no-captions {
    text-align: center;
    color: var(--color-text-muted);
    padding: var(--space-2xl);
}

.caption-file-info {
    font-size: var(--text-xs);
    font-family: var(--font-mono);
    color: var(--color-text-secondary);
    margin: var(--space-sm) 0;
}

/* Caption Controls */
.caption-controls {
    background: var(--color-surface-overlay);
    border-radius: var(--radius-lg);
    padding: var(--space-lg);
    margin-bottom: var(--space-lg);
    border: 1px solid var(--color-border);
}

.caption-controls h3 {
    font-size: var(--text-lg);
    font-weight: 600;
    margin-bottom: var(--space-md);
}

.control-group {
    margin-bottom: var(--space-lg);
}

.control-group label {
    display: block;
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--color-text-secondary);
    margin-bottom: var(--space-xs);
}

.control-select {
    width: 100%;
    padding: var(--space-sm) var(--space-md);
    background: var(--color-surface);
    border: 2px solid var(--color-border);
    border-radius: var(--radius-md);
    color: var(--color-text-primary);
    font-size: var(--text-base);
    font-weight: 500;
    cursor: pointer;
    transition: all var(--transition-base);
}

.control-select:hover {
    border-color: var(--color-primary);
}

.control-select:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(var(--color-primary-rgb), 0.1);
}

.speaker-colors h4 {
    font-size: var(--text-base);
    font-weight: 600;
    margin-bottom: var(--space-sm);
}

.color-selectors {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--space-md);
}

.color-control {
    display: flex;
    flex-direction: column;
    gap: var(--space-xs);
}

.color-control label {
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--color-text-secondary);
}

.color-select {
    transition: all var(--transition-base);
    padding-left: 35px;
    position: relative;
}

/* Color dot indicator */
.color-select::before {
    content: '';
    position: absolute;
    left: 10px;
    top: 50%;
    transform: translateY(-50%);
    width: 12px;
    height: 12px;
    border-radius: 50%;
    border: 2px solid var(--color-border);
}

/* Specific color indicators */
.color-select[value="#FF4500"]::before {
    background-color: #FF4500;
}

.color-select[value="#00BFFF"]::before {
    background-color: #00BFFF;
}

.color-select[value="#FFD700"]::before {
    background-color: #FFD700;
}

.color-select[value="#00FF88"]::before {
    background-color: #00FF88;
}

.color-select[value="#FF1493"]::before {
    background-color: #FF1493;
}

/* Speaker Tabs Styling */
.speaker-tabs-container {
    margin-top: var(--space-lg);
}

.speaker-tabs {
    display: flex;
    gap: var(--space-sm);
    margin-bottom: var(--space-lg);
    border-bottom: 2px solid var(--color-border);
    padding-bottom: var(--space-sm);
}

.speaker-tab {
    padding: var(--space-sm) var(--space-lg);
    background: transparent;
    border: none;
    color: var(--color-text-secondary);
    font-size: var(--text-base);
    font-weight: 500;
    cursor: pointer;
    position: relative;
    transition: all var(--transition-base);
}

.speaker-tab:hover {
    color: var(--color-text-primary);
}

.speaker-tab.active {
    color: var(--tab-color, var(--color-primary));
    font-weight: 600;
}

.speaker-tab.active::after {
    content: '';
    position: absolute;
    bottom: calc(-1 * var(--space-sm) - 2px);
    left: 0;
    right: 0;
    height: 3px;
    background: var(--tab-color, var(--color-primary));
    border-radius: 3px 3px 0 0;
}

/* Speaker Settings Panel */
.speaker-settings-panel {
    display: none;
    animation: fadeIn var(--transition-base) ease-out;
}

.speaker-settings-panel.active {
    display: block;
}

.settings-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--space-md);
    margin-bottom: var(--space-lg);
}

.control-group.full-width {
    grid-column: 1 / -1;
}

/* Font Select Styling */
.font-select {
    font-family: inherit;
}

.font-select option {
    padding: var(--space-xs);
}

/* Color Picker Button */
.color-picker-button {
    width: 100%;
    padding: var(--space-sm) var(--space-md);
    border: 2px solid var(--color-border);
    border-radius: var(--radius-md);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: space-between;
    transition: all var(--transition-base);
    background: var(--color-surface);
    position: relative;
    overflow: hidden;
}

.color-picker-button::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: currentColor;
    opacity: 0.15;
    z-index: 0;
}

.color-picker-button:hover {
    border-color: var(--color-primary);
    transform: translateY(-1px);
}

.color-value {
    font-family: var(--font-mono);
    font-size: var(--text-sm);
    font-weight: 500;
    color: var(--color-text-primary);
    z-index: 1;
    position: relative;
}

/* Apply All Button */
.apply-all-btn {
    width: 100%;
    margin-top: var(--space-md);
}

/* Caption Preview */
.caption-preview-section {
    margin-top: var(--space-xl);
    padding-top: var(--space-xl);
    border-top: 2px solid var(--color-border);
}

.caption-preview-section h4 {
    font-size: var(--text-lg);
    font-weight: 600;
    margin-bottom: var(--space-md);
}

.caption-preview-wrapper {
    background: #000;
    border-radius: var(--radius-lg);
    padding: var(--space-xl);
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 120px;
}

.caption-preview {
    text-align: center;
}

.preview-text {
    font-size: 48px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 2px;
    display: inline-block;
}

/* Color Picker Popup */
.color-picker-popup {
    position: fixed;
    background: var(--color-surface-elevated);
    border: 2px solid var(--color-border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-xl);
    z-index: 1000;
    min-width: 280px;
}

.color-picker-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--space-md);
    border-bottom: 1px solid var(--color-border);
}

.color-picker-title {
    font-size: var(--text-base);
    font-weight: 600;
}

.color-picker-close {
    background: none;
    border: none;
    font-size: var(--text-xl);
    color: var(--color-text-secondary);
    cursor: pointer;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--radius-sm);
    transition: all var(--transition-base);
}

.color-picker-close:hover {
    background: var(--color-surface-overlay);
    color: var(--color-text-primary);
}

.color-picker-body {
    padding: var(--space-lg);
}

.color-wheel-container {
    position: relative;
    margin-bottom: var(--space-md);
    display: flex;
    justify-content: center;
}

#color-wheel {
    border-radius: 50%;
    cursor: crosshair;
}

.color-picker-cursor {
    position: absolute;
    width: 20px;
    height: 20px;
    border: 3px solid white;
    border-radius: 50%;
    pointer-events: none;
    box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.5);
    display: none;
}

.color-controls {
    display: flex;
    gap: var(--space-sm);
    align-items: center;
}

.color-preview-large {
    width: 50px;
    height: 50px;
    border-radius: var(--radius-md);
    border: 2px solid var(--color-border);
    flex-shrink: 0;
}

.color-input {
    flex: 1;
    padding: var(--space-sm);
    background: var(--color-surface);
    border: 2px solid var(--color-border);
    border-radius: var(--radius-md);
    color: var(--color-text-primary);
    font-family: var(--font-mono);
    font-size: var(--text-sm);
    text-transform: uppercase;
}

.color-input:focus {
    outline: none;
    border-color: var(--color-primary);
}

#color-picker-apply {
    flex-shrink: 0;
}

/* Animations */
@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* End Screen Controls */
.video-panel .end-screen-controls {
    background: var(--color-surface-overlay);
    border-radius: var(--radius-lg);
    padding: var(--space-md);
    margin-top: var(--space-md);
}

.video-panel .end-screen-controls h3 {
    font-size: var(--text-base);
    font-weight: 600;
    margin-bottom: var(--space-xs);
}

.video-panel .section-description {
    font-size: var(--text-sm);
    color: var(--color-text-secondary);
    margin-bottom: var(--space-sm);
}

/* Keep the original end-screen-controls styles for the settings */
.end-screen-controls {
    background: var(--color-surface-overlay);
    border-radius: var(--radius-lg);
    padding: var(--space-lg);
    margin-bottom: var(--space-lg);
    border: 1px solid var(--color-border);
}

.end-screen-controls h3 {
    font-size: var(--text-lg);
    font-weight: 600;
    margin-bottom: var(--space-xs);
}

.section-description {
    font-size: var(--text-sm);
    color: var(--color-text-secondary);
    margin-bottom: var(--space-md);
}

.checkbox-label {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    cursor: pointer;
    font-size: var(--text-base);
    font-weight: 500;
}

.control-checkbox {
    width: 20px;
    height: 20px;
    cursor: pointer;
}

.end-screen-settings {
    margin-top: var(--space-lg);
    padding-top: var(--space-lg);
    border-top: 1px solid var(--color-border);
}

.control-textarea {
    width: 100%;
    padding: var(--space-sm);
    background: var(--color-surface);
    border: 2px solid var(--color-border);
    border-radius: var(--radius-md);
    color: var(--color-text-primary);
    font-size: var(--text-base);
    line-height: 1.5;
    resize: vertical;
    transition: all var(--transition-base);
    font-family: inherit;
}

.control-textarea:focus {
    outline: none;
    border-color: var(--color-primary);
    background: var(--color-surface-elevated);
}

.control-hint {
    display: block;
    font-size: var(--text-xs);
    color: var(--color-text-muted);
    margin-top: var(--space-xs);
}

.slider-container {
    display: flex;
    align-items: center;
    gap: var(--space-md);
}

.control-slider {
    flex: 1;
    -webkit-appearance: none;
    appearance: none;
    width: 100%;
    height: 6px;
    background: var(--color-surface);
    border-radius: 3px;
    outline: none;
    transition: all var(--transition-base);
}

.control-slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 20px;
    height: 20px;
    background: var(--color-primary);
    border-radius: 50%;
    cursor: pointer;
    transition: all var(--transition-base);
}

.control-slider::-webkit-slider-thumb:hover {
    transform: scale(1.2);
    box-shadow: 0 0 0 4px rgba(var(--color-primary-rgb), 0.2);
}

.control-slider::-moz-range-thumb {
    width: 20px;
    height: 20px;
    background: var(--color-primary);
    border-radius: 50%;
    cursor: pointer;
    border: none;
    transition: all var(--transition-base);
}

.control-slider::-moz-range-thumb:hover {
    transform: scale(1.2);
    box-shadow: 0 0 0 4px rgba(var(--color-primary-rgb), 0.2);
}

.slider-value {
    font-size: var(--text-base);
    font-weight: 600;
    color: var(--color-primary);
    min-width: 45px;
    text-align: right;
}

/* Edit Actions */
.edit-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: var(--space-lg);
    border-top: 1px solid var(--color-border);
}

.action-group {
    display: flex;
    gap: var(--space-md);
}

/* Update Progress */
.update-progress {
    margin-top: var(--space-lg);
    padding: var(--space-md);
    background: var(--color-surface-overlay);
    border-radius: var(--radius-lg);
}

.update-status {
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
}

.update-text {
    font-size: var(--text-sm);
    color: var(--color-text-secondary);
}

.update-progress-bar {
    height: 4px;
    background: var(--color-surface);
    border-radius: 2px;
    overflow: hidden;
}

.update-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--color-primary) 0%, var(--color-secondary) 100%);
    transition: width var(--transition-base);
}

/* Auth Prompt Overlay */
.auth-prompt-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 999;
    backdrop-filter: blur(4px);
}

.auth-prompt-modal {
    background: var(--color-surface-elevated);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-xl);
    padding: var(--space-2xl);
    max-width: 500px;
    width: 90%;
    box-shadow: var(--shadow-xl);
    animation: slideIn var(--transition-base) ease-out;
}

.auth-prompt-modal h2 {
    font-size: var(--text-2xl);
    font-weight: 700;
    margin-bottom: var(--space-md);
    text-align: center;
}

.auth-prompt-modal p {
    text-align: center;
    color: var(--color-text-secondary);
    margin-bottom: var(--space-xl);
}

.auth-benefits {
    background: var(--color-surface-overlay);
    border-radius: var(--radius-lg);
    padding: var(--space-lg);
    margin-bottom: var(--space-xl);
}

.auth-benefits h4 {
    font-size: var(--text-base);
    font-weight: 600;
    margin-bottom: var(--space-md);
    color: var(--color-primary);
}

.auth-benefits ul {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
}

.auth-benefits li {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
    font-size: var(--text-sm);
    color: var(--color-text-secondary);
}

.auth-benefits li svg {
    color: var(--color-success);
    flex-shrink: 0;
}

.auth-actions {
    display: flex;
    flex-direction: column;
    gap: var(--space-md);
}

.auth-actions .btn {
    width: 100%;
    justify-content: center;
}

/* Responsive */
@media (max-width: 1024px) {
    .edit-container {
        grid-template-columns: 1fr;
    }
    
    .video-panel {
        order: 1;
    }
    
    .caption-panel {
        order: 2;
    }
    
    .color-selectors {
        grid-template-columns: 1fr;
        gap: var(--space-sm);
    }
}

@media (max-width: 768px) {
    .video-info-grid {
        grid-template-columns: 1fr;
    }
    
    .edit-actions {
        flex-direction: column;
    }
    
    .action-group {
        width: 100%;
        flex-direction: column;
    }
    
    .action-group .btn {
        width: 100%;
    }
}
</style>
`;

// Add styles to document
document.head.insertAdjacentHTML('beforeend', editPageStyles);

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.editPage = new EditPage();
});
