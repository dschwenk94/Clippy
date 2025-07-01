// Caption Position Sync Handler - Ensures perfect alignment between slider and indicator

class CaptionPositionSync {
    constructor(editPage) {
        this.editPage = editPage;
        this.captionPositionPercent = 80; // Default 80% from top (bottom position)
        this.videoHeight = 0;
        this.initializePositionSlider();
    }
    
    initializePositionSlider() {
        const slider = document.getElementById('caption-position-slider');
        const indicator = document.getElementById('caption-position-indicator');
        const video = document.getElementById('clip-video');
        const sliderWrapper = document.querySelector('.slider-vertical-wrapper');
        
        if (!slider || !indicator || !video) {
            console.warn('Caption position elements not found');
            return;
        }
        
        // Set initial slider value (inverted because visual is bottom to top)
        slider.value = 100 - this.captionPositionPercent;
        
        // Update on video load
        video.addEventListener('loadedmetadata', () => {
            this.syncSliderHeight();
            this.updateIndicatorPosition(this.captionPositionPercent);
        });
        
        // Handle slider input
        slider.addEventListener('input', (e) => {
            const sliderValue = parseInt(e.target.value);
            // Invert: slider 100 (visual top) = 0% from top
            this.captionPositionPercent = 100 - sliderValue;
            this.updateIndicatorPosition(this.captionPositionPercent);
            this.editPage.hasUnsavedChanges = true;
            
            console.log('Caption position update:', {
                sliderValue: sliderValue,
                percentFromTop: this.captionPositionPercent + '%',
                expectedMarginV: this.calculateMarginV(this.captionPositionPercent)
            });
        });
        
        // Handle window resize
        window.addEventListener('resize', () => {
            this.syncSliderHeight();
            this.updateIndicatorPosition(this.captionPositionPercent);
        });
        
        // Initial sync
        setTimeout(() => {
            this.syncSliderHeight();
            this.updateIndicatorPosition(this.captionPositionPercent);
        }, 100);
    }
    
    syncSliderHeight() {
        const video = document.getElementById('clip-video');
        const sliderWrapper = document.querySelector('.slider-vertical-wrapper');
        
        if (!video || !sliderWrapper) return;
        
        // Wait for video to be fully loaded
        if (video.videoHeight === 0) {
            setTimeout(() => this.syncSliderHeight(), 100);
            return;
        }
        
        const videoRect = video.getBoundingClientRect();
        this.videoHeight = videoRect.height;
        
        // Don't override CSS - let flexbox handle the sizing
        // Just store the video height for other calculations
        console.log('Video height detected:', this.videoHeight);
    }
    
    updateIndicatorPosition(percent) {
        const indicator = document.getElementById('caption-position-indicator');
        const video = document.getElementById('clip-video');
        
        if (!indicator || !video) return;
        
        const videoRect = video.getBoundingClientRect();
        if (videoRect.height === 0) {
            setTimeout(() => this.updateIndicatorPosition(percent), 100);
            return;
        }
        
        // Direct percentage to pixel conversion
        const position = (percent / 100) * videoRect.height;
        indicator.style.top = `${position}px`;
        
        // Also show the expected ASS margin value
        const expectedMargin = this.calculateMarginV(percent);
        
        console.log('Position sync:', {
            percentFromTop: percent + '%',
            pixelPosition: position.toFixed(1) + 'px',
            videoHeight: videoRect.height + 'px',
            expectedASSMargin: expectedMargin
        });
    }
    
    calculateMarginV(percentFromTop) {
        // This should match the backend calculation
        const videoHeightEstimate = 720;
        const positionFromTop = (percentFromTop / 100) * videoHeightEstimate;
        const marginFromBottom = videoHeightEstimate - positionFromTop;
        let marginV = Math.round(marginFromBottom * 0.35);
        
        // Ensure reasonable bounds
        marginV = Math.max(10, Math.min(marginV, 250));
        
        return marginV;
    }
    
    getCaptionPosition() {
        return this.captionPositionPercent;
    }
}

// Make it available globally
window.CaptionPositionSync = CaptionPositionSync;
