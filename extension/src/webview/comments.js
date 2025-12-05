/**
 * CommentPanel Component
 * 
 * Sprint 3, Phase 1: Comment Display & Basic Interaction
 * 
 * A UI component that displays Word document comments in a sidebar panel.
 * Features:
 * - Flat list of comments with author, date, status
 * - Click-to-scroll to referenced text
 * - Resolve/unresolve actions
 * - Comment-block highlighting
 * - Filtering by status (all/active/resolved)
 */

class CommentPanel {
    /**
     * Create a CommentPanel
     * @param {HTMLElement} container - The container element to render into
     * @param {Object} options - Configuration options
     * @param {Function} options.onCommentClick - Called when a comment is clicked
     * @param {Function} options.onScrollToBlock - Called to scroll to a block by para_id
     * @param {Function} options.onResolve - Called when resolve action is triggered
     * @param {Function} options.onUnresolve - Called when unresolve action is triggered
     * @param {Function} options.onHighlightBlock - Called to highlight a block by para_id
     */
    constructor(container, options = {}) {
        this.container = container;
        this.options = options;
        this.comments = [];
        this.filter = 'all';
        this.selectedCommentId = null;
        
        this._render();
    }
    
    /**
     * Set the comments to display
     * @param {Array} comments - Array of comment objects
     */
    setComments(comments) {
        this.comments = comments || [];
        
        // Check if selected comment still exists
        if (this.selectedCommentId) {
            const stillExists = this.comments.some(c => c.id === this.selectedCommentId);
            if (!stillExists) {
                this.selectedCommentId = null;
                if (this.options.onHighlightBlock) {
                    this.options.onHighlightBlock(null);
                }
            }
        }
        
        this._renderComments();
        
        // Re-apply selection visual if comment still exists
        if (this.selectedCommentId) {
            this._applySelection(this.selectedCommentId);
        }
    }
    
    /**
     * Set the filter for displaying comments
     * @param {string} filter - 'all', 'active', or 'resolved'
     */
    setFilter(filter) {
        this.filter = filter;
        this._updateFilterButtons();
        this._renderComments();
    }
    
    /**
     * Select a comment by ID
     * @param {string} commentId - The ID of the comment to select
     */
    selectComment(commentId) {
        // Clear previous selection
        const prevSelected = this.panelElement.querySelector('.comment-selected');
        if (prevSelected) {
            prevSelected.classList.remove('comment-selected');
        }
        
        this.selectedCommentId = commentId;
        this._applySelection(commentId);
        
        // Find the comment to get its para_id
        const comment = this.comments.find(c => c.id === commentId);
        if (comment && comment.para_id && this.options.onHighlightBlock) {
            this.options.onHighlightBlock(comment.para_id);
        }
    }
    
    /**
     * Clear the current selection
     */
    clearSelection() {
        const prevSelected = this.panelElement.querySelector('.comment-selected');
        if (prevSelected) {
            prevSelected.classList.remove('comment-selected');
        }
        
        this.selectedCommentId = null;
        
        if (this.options.onHighlightBlock) {
            this.options.onHighlightBlock(null);
        }
    }
    
    /**
     * Update the status of a comment
     * @param {string} commentId - The ID of the comment
     * @param {string} status - 'active' or 'resolved'
     */
    updateCommentStatus(commentId, status) {
        const comment = this.comments.find(c => c.id === commentId);
        if (comment) {
            comment.status = status;
            comment.is_resolved = status === 'resolved';
            this._renderComments();
        }
    }
    
    // ========================================================================
    // Private Methods
    // ========================================================================
    
    _render() {
        // Create the main panel structure
        this.panelElement = this._createElement('div', 'comment-panel');
        this.container.appendChild(this.panelElement);
        
        // Header with title and filter buttons
        this._renderHeader();
        
        // Comments list container
        this.listElement = this._createElement('div', 'comment-list');
        this.panelElement.appendChild(this.listElement);
    }
    
    _renderHeader() {
        this.headerElement = this._createElement('div', 'comment-panel-header');
        
        // Title with count
        this.titleElement = this._createElement('span', 'comment-panel-title');
        this.titleElement.textContent = 'Comments (0)';
        this.headerElement.appendChild(this.titleElement);
        
        // Filter buttons
        const filterContainer = this._createElement('div', 'comment-filter-buttons');
        
        this.filterAllBtn = this._createElement('button', 'filter-btn filter-btn-all active');
        this.filterAllBtn.textContent = 'All';
        this.filterAllBtn.addEventListener('click', () => this.setFilter('all'));
        filterContainer.appendChild(this.filterAllBtn);
        
        this.filterActiveBtn = this._createElement('button', 'filter-btn filter-btn-active');
        this.filterActiveBtn.textContent = 'Active';
        this.filterActiveBtn.addEventListener('click', () => this.setFilter('active'));
        filterContainer.appendChild(this.filterActiveBtn);
        
        this.filterResolvedBtn = this._createElement('button', 'filter-btn filter-btn-resolved');
        this.filterResolvedBtn.textContent = 'Resolved';
        this.filterResolvedBtn.addEventListener('click', () => this.setFilter('resolved'));
        filterContainer.appendChild(this.filterResolvedBtn);
        
        this.headerElement.appendChild(filterContainer);
        this.panelElement.appendChild(this.headerElement);
    }
    
    _renderComments() {
        // Clear existing content
        this.listElement.innerHTML = '';
        
        // Filter comments
        const filteredComments = this._getFilteredComments();
        
        // Update title count
        this.titleElement.textContent = `Comments (${this.comments.length})`;
        
        // Show empty state if no comments
        if (filteredComments.length === 0) {
            const emptyElement = this._createElement('div', 'comment-panel-empty');
            emptyElement.textContent = 'No comments';
            this.listElement.appendChild(emptyElement);
            return;
        }
        
        // Render each comment
        filteredComments.forEach(comment => {
            const itemElement = this._renderCommentItem(comment);
            this.listElement.appendChild(itemElement);
        });
    }
    
    _renderCommentItem(comment) {
        const isResolved = comment.is_resolved || comment.status === 'resolved';
        const statusClass = isResolved ? 'status-resolved' : 'status-active';
        
        const item = this._createElement('div', `comment-item ${statusClass}`);
        item.dataset.commentId = comment.id;
        
        if (comment.para_id) {
            item.dataset.paraId = comment.para_id;
        }
        
        // Header row: author, date, status badge
        const header = this._createElement('div', 'comment-header');
        
        const author = this._createElement('span', 'comment-author');
        author.textContent = comment.author || 'Unknown';
        header.appendChild(author);
        
        const date = this._createElement('span', 'comment-date');
        date.textContent = this._formatDate(comment.date);
        header.appendChild(date);
        
        const badge = this._createElement('span', 'comment-status-badge');
        badge.textContent = isResolved ? 'Resolved' : 'Active';
        header.appendChild(badge);
        
        item.appendChild(header);
        
        // Reference text (if available)
        if (comment.para_id && comment.reference_text) {
            const reference = this._createElement('div', 'comment-reference');
            reference.textContent = this._truncateText(comment.reference_text, 80);
            item.appendChild(reference);
        }
        
        // Comment text
        const text = this._createElement('div', 'comment-text');
        text.textContent = comment.text || '';
        item.appendChild(text);
        
        // Action buttons
        const actions = this._createElement('div', 'comment-actions');
        
        if (isResolved) {
            const unresolveBtn = this._createElement('button', 'comment-action comment-action-unresolve');
            unresolveBtn.textContent = 'Unresolve';
            unresolveBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (this.options.onUnresolve) {
                    // Use para_id - the stable identifier for threading and status
                    this.options.onUnresolve(comment.para_id);
                }
            });
            actions.appendChild(unresolveBtn);
        } else {
            const resolveBtn = this._createElement('button', 'comment-action comment-action-resolve');
            resolveBtn.textContent = 'Resolve';
            resolveBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (this.options.onResolve) {
                    // Use para_id - the stable identifier for threading and status
                    this.options.onResolve(comment.para_id);
                }
            });
            actions.appendChild(resolveBtn);
        }
        
        item.appendChild(actions);
        
        // Click handler for the whole item
        item.addEventListener('click', () => {
            if (this.options.onCommentClick) {
                this.options.onCommentClick(comment);
            }
            
            if (comment.para_id && this.options.onScrollToBlock) {
                this.options.onScrollToBlock(comment.para_id);
            }
        });
        
        return item;
    }
    
    _applySelection(commentId) {
        const item = this.panelElement.querySelector(`[data-comment-id="${commentId}"]`);
        if (item) {
            item.classList.add('comment-selected');
            item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }
    
    _updateFilterButtons() {
        // Remove active class from all
        this.filterAllBtn.classList.remove('active');
        this.filterActiveBtn.classList.remove('active');
        this.filterResolvedBtn.classList.remove('active');
        
        // Add active class to current filter
        switch (this.filter) {
            case 'all':
                this.filterAllBtn.classList.add('active');
                break;
            case 'active':
                this.filterActiveBtn.classList.add('active');
                break;
            case 'resolved':
                this.filterResolvedBtn.classList.add('active');
                break;
        }
    }
    
    _getFilteredComments() {
        if (this.filter === 'all') {
            return this.comments;
        }
        
        return this.comments.filter(comment => {
            const isResolved = comment.is_resolved || comment.status === 'resolved';
            if (this.filter === 'resolved') {
                return isResolved;
            } else {
                return !isResolved;
            }
        });
    }
    
    _createElement(tag, className) {
        const element = document.createElement(tag);
        if (className) {
            className.split(' ').forEach(cls => {
                if (cls) element.classList.add(cls);
            });
        }
        return element;
    }
    
    _formatDate(dateString) {
        if (!dateString) return '';
        
        try {
            const date = new Date(dateString);
            const options = { month: 'short', day: 'numeric', year: 'numeric' };
            return date.toLocaleDateString('en-US', options);
        } catch (e) {
            return dateString;
        }
    }
    
    _truncateText(text, maxLength) {
        if (!text) return '';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength - 3) + '...';
    }
}

// Export for both browser and Node.js environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CommentPanel };
}

// Also expose on window for browser
if (typeof window !== 'undefined') {
    window.CommentPanel = CommentPanel;
}
