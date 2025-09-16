/**
 * Audio Downloader Main JavaScript
 * 
 * This file contains common JavaScript functionality for the audio downloader application.
 */

// Global variables
let downloadStatusInterval = null;
let sessionStatusInterval = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeTooltips();
    initializeFormValidation();
    initializeAutoRefresh();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

/**
 * Initialize auto-refresh for status updates
 */
function initializeAutoRefresh() {
    // Auto-refresh download status every 5 seconds if there are active downloads
    const activeDownloads = document.querySelectorAll('[data-download-status="downloading"]');
    if (activeDownloads.length > 0) {
        startDownloadStatusRefresh();
    }
    
    // Auto-refresh session status every 10 seconds if there are active sessions
    const activeSessions = document.querySelectorAll('[data-session-status="in_progress"]');
    if (activeSessions.length > 0) {
        startSessionStatusRefresh();
    }
}

/**
 * Start refreshing download status
 */
function startDownloadStatusRefresh() {
    if (downloadStatusInterval) {
        clearInterval(downloadStatusInterval);
    }
    
    downloadStatusInterval = setInterval(() => {
        refreshDownloadStatuses();
    }, 5000);
}

/**
 * Start refreshing session status
 */
function startSessionStatusRefresh() {
    if (sessionStatusInterval) {
        clearInterval(sessionStatusInterval);
    }
    
    sessionStatusInterval = setInterval(() => {
        refreshSessionStatuses();
    }, 10000);
}

/**
 * Refresh download statuses
 */
function refreshDownloadStatuses() {
    const downloadElements = document.querySelectorAll('[data-download-id]');
    
    downloadElements.forEach(element => {
        const downloadId = element.getAttribute('data-download-id');
        if (downloadId) {
            fetchDownloadStatus(downloadId);
        }
    });
}

/**
 * Refresh session statuses
 */
function refreshSessionStatuses() {
    const sessionElements = document.querySelectorAll('[data-session-id]');
    
    sessionElements.forEach(element => {
        const sessionId = element.getAttribute('data-session-id');
        if (sessionId) {
            fetchSessionStatus(sessionId);
        }
    });
}

/**
 * Fetch download status via AJAX
 */
function fetchDownloadStatus(downloadId) {
    fetch(`/downloads/${downloadId}/status/`)
        .then(response => response.json())
        .then(data => {
            updateDownloadStatus(downloadId, data);
        })
        .catch(error => {
            console.error('Error fetching download status:', error);
        });
}

/**
 * Fetch session status via AJAX
 */
function fetchSessionStatus(sessionId) {
    fetch(`/sessions/${sessionId}/status/`)
        .then(response => response.json())
        .then(data => {
            updateSessionStatus(sessionId, data);
        })
        .catch(error => {
            console.error('Error fetching session status:', error);
        });
}

/**
 * Update download status in UI
 */
function updateDownloadStatus(downloadId, data) {
    const statusElement = document.querySelector(`[data-download-id="${downloadId}"] .download-status`);
    const progressElement = document.querySelector(`[data-download-id="${downloadId}"] .download-progress`);
    const actionButtons = document.querySelector(`[data-download-id="${downloadId}"] .download-actions`);
    
    if (statusElement) {
        statusElement.textContent = data.status;
        statusElement.className = `badge bg-${getStatusColor(data.status)} download-status`;
    }
    
    if (progressElement && data.progress !== undefined) {
        progressElement.style.width = `${data.progress}%`;
        progressElement.setAttribute('aria-valuenow', data.progress);
    }
    
    if (actionButtons) {
        updateActionButtons(actionButtons, data.status);
    }
    
    // Stop refreshing if download is completed, failed, or cancelled
    if (['completed', 'failed', 'cancelled'].includes(data.status)) {
        stopDownloadStatusRefresh();
    }
}

/**
 * Update session status in UI
 */
function updateSessionStatus(sessionId, data) {
    const statusElement = document.querySelector(`[data-session-id="${sessionId}"] .session-status`);
    const progressElement = document.querySelector(`[data-session-id="${sessionId}"] .session-progress`);
    const statsElement = document.querySelector(`[data-session-id="${sessionId}"] .session-stats`);
    
    if (statusElement) {
        statusElement.textContent = data.status;
        statusElement.className = `badge bg-${getStatusColor(data.status)} session-status`;
    }
    
    if (progressElement) {
        progressElement.style.width = `${data.progress_percentage}%`;
        progressElement.setAttribute('aria-valuenow', data.progress_percentage);
    }
    
    if (statsElement) {
        statsElement.innerHTML = `
            <div class="col-6">
                <div class="border-end">
                    <h6 class="mb-0 text-primary">${data.total_downloads}</h6>
                    <small class="text-muted">Total</small>
                </div>
            </div>
            <div class="col-6">
                <h6 class="mb-0 text-success">${data.completed_downloads}</h6>
                <small class="text-muted">Completed</small>
            </div>
        `;
    }
    
    // Stop refreshing if session is completed or failed
    if (['completed', 'failed'].includes(data.status)) {
        stopSessionStatusRefresh();
    }
}

/**
 * Get color class for status
 */
function getStatusColor(status) {
    const statusColors = {
        'pending': 'primary',
        'downloading': 'warning',
        'in_progress': 'warning',
        'completed': 'success',
        'failed': 'danger',
        'cancelled': 'secondary'
    };
    return statusColors[status] || 'secondary';
}

/**
 * Update action buttons based on status
 */
function updateActionButtons(container, status) {
    const startBtn = container.querySelector('.btn-start');
    const cancelBtn = container.querySelector('.btn-cancel');
    const downloadBtn = container.querySelector('.btn-download');
    
    if (startBtn) {
        startBtn.style.display = status === 'pending' ? 'inline-block' : 'none';
    }
    
    if (cancelBtn) {
        cancelBtn.style.display = status === 'downloading' ? 'inline-block' : 'none';
    }
    
    if (downloadBtn) {
        downloadBtn.style.display = status === 'completed' ? 'inline-block' : 'none';
    }
}

/**
 * Stop download status refresh
 */
function stopDownloadStatusRefresh() {
    if (downloadStatusInterval) {
        clearInterval(downloadStatusInterval);
        downloadStatusInterval = null;
    }
}

/**
 * Stop session status refresh
 */
function stopSessionStatusRefresh() {
    if (sessionStatusInterval) {
        clearInterval(sessionStatusInterval);
        sessionStatusInterval = null;
    }
}

/**
 * Show loading state
 */
function showLoading(element) {
    element.classList.add('loading');
    const spinner = document.createElement('div');
    spinner.className = 'spinner-border spinner-border-sm me-2';
    element.insertBefore(spinner, element.firstChild);
}

/**
 * Hide loading state
 */
function hideLoading(element) {
    element.classList.remove('loading');
    const spinner = element.querySelector('.spinner-border');
    if (spinner) {
        spinner.remove();
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Format duration
 */
function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
}

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle function
 */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Export functions for global use
window.AudioDownloader = {
    showLoading,
    hideLoading,
    showNotification,
    formatFileSize,
    formatDuration,
    debounce,
    throttle,
    startDownloadStatusRefresh,
    stopDownloadStatusRefresh,
    startSessionStatusRefresh,
    stopSessionStatusRefresh
};
