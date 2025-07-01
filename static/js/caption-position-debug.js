// Caption Position Visual Debug Helper
// This helps visualize where captions will appear relative to the indicator

class CaptionPositionDebug {
    constructor() {
        this.debugOverlay = null;
        this.isDebugging = false;
    }
    
    toggleDebug() {
        if (this.isDebugging) {
            this.hideDebug();
        } else {
            this.showDebug();
        }
    }
    
    showDebug() {
        const video = document.getElementById('clip-video');
        const videoWrapper = document.querySelector('.video-wrapper');
        const indicator = document.getElementById('caption-position-indicator');
        
        if (!video || !videoWrapper || !indicator) return;
        
        // Create debug overlay
        this.debugOverlay = document.createElement('div');
        this.debugOverlay.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
            z-index: 1000;
        `;
        
        // Get indicator position
        const indicatorRect = indicator.getBoundingClientRect();
        const videoRect = video.getBoundingClientRect();
        const relativeTop = indicatorRect.top - videoRect.top;
        
        // Create a mock caption at the indicator position
        const mockCaption = document.createElement('div');
        mockCaption.style.cssText = `
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 183, 255, 0.9);
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            font-family: Arial Black, sans-serif;
            font-size: 20px;
            font-weight: bold;
            text-align: center;
            white-space: nowrap;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
            border: 3px solid #000;
        `;
        mockCaption.textContent = 'Caption Preview';
        
        // Position the mock caption where the actual caption should appear
        // The indicator shows where the TOP of the caption should be
        mockCaption.style.top = `${relativeTop}px`;
        
        // Add percentage label
        const percentLabel = document.createElement('div');
        percentLabel.style.cssText = `
            position: absolute;
            right: 10px;
            background: rgba(0,0,0,0.8);
            color: #ff6b35;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        `;
        
        // Get current position percentage
        const positionSync = window.captionPositionSync || this.findCaptionPositionSync();
        const percent = positionSync ? positionSync.getCaptionPosition() : 80;
        percentLabel.textContent = `${percent}% from top`;
        percentLabel.style.top = `${relativeTop - 20}px`;
        
        this.debugOverlay.appendChild(mockCaption);
        this.debugOverlay.appendChild(percentLabel);
        videoWrapper.appendChild(this.debugOverlay);
        
        this.isDebugging = true;
        
        // Auto-hide after 3 seconds
        setTimeout(() => this.hideDebug(), 3000);
    }
    
    hideDebug() {
        if (this.debugOverlay) {
            this.debugOverlay.remove();
            this.debugOverlay = null;
        }
        this.isDebugging = false;
    }
    
    findCaptionPositionSync() {
        // Try to find the caption position sync instance
        if (window.editPage && window.editPage.captionPositionSync) {
            return window.editPage.captionPositionSync;
        }
        return null;
    }
}

// Initialize and attach to toggle button
document.addEventListener('DOMContentLoaded', () => {
    const debugHelper = new CaptionPositionDebug();
    
    // Attach to caption toggle button
    const toggleButton = document.querySelector('button:has(.toggle-text)');
    if (toggleButton) {
        toggleButton.addEventListener('click', () => {
            // Show debug overlay briefly when toggling captions
            setTimeout(() => debugHelper.showDebug(), 100);
        });
    }
    
    // Also add keyboard shortcut (Ctrl+D) for debugging
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'd') {
            e.preventDefault();
            debugHelper.toggleDebug();
        }
    });
    
    // Make it globally available
    window.captionPositionDebug = debugHelper;
});
