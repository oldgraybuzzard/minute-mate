/**
 * Advanced Search Manager
 * Handles global search, advanced filtering, and search analytics
 */

class SearchManager {
    constructor() {
        this.searchHistory = JSON.parse(localStorage.getItem('searchHistory') || '[]');
        this.searchFilters = {
            dateRange: '',
            status: '',
            attendees: '',
            tags: '',
            duration: '',
            hasTranscript: null,
            hasActionItems: null
        };
        this.searchResults = [];
        this.searchIndex = new Map();
        this.popularSearches = JSON.parse(localStorage.getItem('popularSearches') || '[]');
        
        this.initializeSearch();
    }

    initializeSearch() {
        this.buildSearchIndex();
        this.setupGlobalSearch();
    }

    // Build search index for faster searching
    async buildSearchIndex() {
        try {
            const response = await fetch('/api/search/index', {
                credentials: 'include'
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.searchIndex = new Map(result.data.index);
                }
            }
        } catch (error) {
            console.error('Error building search index:', error);
        }
    }

    setupGlobalSearch() {
        // Create global search shortcut (Ctrl/Cmd + K)
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.openGlobalSearch();
            }
        });
    }

    openGlobalSearch() {
        const searchModal = this.createSearchModal();
        document.body.appendChild(searchModal);
        
        // Focus search input
        const searchInput = searchModal.querySelector('.global-search-input');
        searchInput.focus();
        
        // Load recent searches
        this.loadRecentSearches(searchModal);
    }

    createSearchModal() {
        const modal = document.createElement('div');
        modal.className = 'search-modal-overlay';
        modal.innerHTML = `
            <div class="search-modal">
                <div class="search-header">
                    <div class="search-input-container">
                        <i class="fas fa-search search-icon"></i>
                        <input type="text" class="global-search-input" placeholder="Search meetings, transcripts, action items..." autocomplete="off">
                        <button class="search-close" onclick="this.closest('.search-modal-overlay').remove()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="search-filters-toggle">
                        <button class="btn secondary small" id="toggle-search-filters">
                            <i class="fas fa-filter"></i> Filters
                        </button>
                    </div>
                </div>
                
                <div class="search-filters" id="search-filters" style="display: none;">
                    <div class="filter-row">
                        <div class="filter-group">
                            <label>Date Range</label>
                            <select id="search-date-range">
                                <option value="">Any time</option>
                                <option value="today">Today</option>
                                <option value="week">This week</option>
                                <option value="month">This month</option>
                                <option value="quarter">This quarter</option>
                                <option value="year">This year</option>
                            </select>
                        </div>
                        <div class="filter-group">
                            <label>Status</label>
                            <select id="search-status">
                                <option value="">All statuses</option>
                                <option value="completed">Completed</option>
                                <option value="processing">Processing</option>
                                <option value="failed">Failed</option>
                            </select>
                        </div>
                        <div class="filter-group">
                            <label>Duration</label>
                            <select id="search-duration">
                                <option value="">Any duration</option>
                                <option value="short">< 30 minutes</option>
                                <option value="medium">30-60 minutes</option>
                                <option value="long">> 60 minutes</option>
                            </select>
                        </div>
                    </div>
                    <div class="filter-row">
                        <div class="filter-group">
                            <label>Content Type</label>
                            <div class="checkbox-group">
                                <label class="checkbox-label">
                                    <input type="checkbox" id="has-transcript"> Has Transcript
                                </label>
                                <label class="checkbox-label">
                                    <input type="checkbox" id="has-action-items"> Has Action Items
                                </label>
                                <label class="checkbox-label">
                                    <input type="checkbox" id="has-decisions"> Has Decisions
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="search-content">
                    <div class="search-suggestions" id="search-suggestions">
                        <div class="suggestions-section">
                            <h4>Recent Searches</h4>
                            <div class="recent-searches" id="recent-searches"></div>
                        </div>
                        <div class="suggestions-section">
                            <h4>Popular Searches</h4>
                            <div class="popular-searches" id="popular-searches"></div>
                        </div>
                    </div>
                    
                    <div class="search-results" id="search-results" style="display: none;">
                        <div class="results-header">
                            <span class="results-count">0 results</span>
                            <div class="results-sort">
                                <select id="results-sort">
                                    <option value="relevance">Relevance</option>
                                    <option value="date">Date</option>
                                    <option value="title">Title</option>
                                </select>
                            </div>
                        </div>
                        <div class="results-list" id="results-list"></div>
                    </div>
                </div>
            </div>
        `;

        // Setup event listeners
        this.setupSearchModalEvents(modal);
        
        return modal;
    }

    setupSearchModalEvents(modal) {
        const searchInput = modal.querySelector('.global-search-input');
        const filtersToggle = modal.querySelector('#toggle-search-filters');
        const filtersContainer = modal.querySelector('#search-filters');
        const resultsContainer = modal.querySelector('#search-results');
        const suggestionsContainer = modal.querySelector('#search-suggestions');

        // Search input with debouncing
        searchInput.addEventListener('input', window.loadingManager.debounce((e) => {
            const query = e.target.value.trim();
            if (query.length >= 2) {
                this.performSearch(query, modal);
                suggestionsContainer.style.display = 'none';
                resultsContainer.style.display = 'block';
            } else {
                suggestionsContainer.style.display = 'block';
                resultsContainer.style.display = 'none';
            }
        }, 300));

        // Filters toggle
        filtersToggle.addEventListener('click', () => {
            const isVisible = filtersContainer.style.display !== 'none';
            filtersContainer.style.display = isVisible ? 'none' : 'block';
            filtersToggle.innerHTML = isVisible ? 
                '<i class="fas fa-filter"></i> Filters' : 
                '<i class="fas fa-filter"></i> Hide Filters';
        });

        // Filter changes
        modal.querySelectorAll('select, input[type="checkbox"]').forEach(element => {
            element.addEventListener('change', () => {
                this.updateSearchFilters(modal);
                const query = searchInput.value.trim();
                if (query.length >= 2) {
                    this.performSearch(query, modal);
                }
            });
        });

        // Close modal on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                modal.remove();
            }
        });

        // Close modal on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    updateSearchFilters(modal) {
        this.searchFilters = {
            dateRange: modal.querySelector('#search-date-range').value,
            status: modal.querySelector('#search-status').value,
            duration: modal.querySelector('#search-duration').value,
            hasTranscript: modal.querySelector('#has-transcript').checked,
            hasActionItems: modal.querySelector('#has-action-items').checked,
            hasDecisions: modal.querySelector('#has-decisions').checked
        };
    }

    async performSearch(query, modal) {
        try {
            // Add to search history
            this.addToSearchHistory(query);

            // Show loading
            const resultsList = modal.querySelector('#results-list');
            resultsList.innerHTML = '<div class="search-loading">Searching...</div>';

            // Build search parameters
            const params = new URLSearchParams({
                q: query,
                ...this.searchFilters
            });

            const response = await fetch(`/api/search/global?${params}`, {
                credentials: 'include'
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.displaySearchResults(result.data, modal);
                    this.updateSearchAnalytics(query, result.data.results.length);
                }
            }
        } catch (error) {
            console.error('Search error:', error);
            const resultsList = modal.querySelector('#results-list');
            resultsList.innerHTML = '<div class="search-error">Search failed. Please try again.</div>';
        }
    }

    displaySearchResults(data, modal) {
        const resultsList = modal.querySelector('#results-list');
        const resultsCount = modal.querySelector('.results-count');
        
        resultsCount.textContent = `${data.results.length} result${data.results.length !== 1 ? 's' : ''}`;

        if (data.results.length === 0) {
            resultsList.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search"></i>
                    <h3>No results found</h3>
                    <p>Try adjusting your search terms or filters</p>
                </div>
            `;
            return;
        }

        const resultsHtml = data.results.map(result => `
            <div class="search-result-item" onclick="searchManager.openSearchResult('${result.id}', '${result.type}')">
                <div class="result-header">
                    <h4 class="result-title">${this.highlightSearchTerms(result.title, data.query)}</h4>
                    <span class="result-type">${result.type}</span>
                </div>
                <div class="result-meta">
                    <span class="result-date">${new Date(result.date).toLocaleDateString()}</span>
                    ${result.duration ? `<span class="result-duration">${result.duration} min</span>` : ''}
                    <span class="result-score">Score: ${Math.round(result.score * 100)}%</span>
                </div>
                <div class="result-snippet">
                    ${this.highlightSearchTerms(result.snippet, data.query)}
                </div>
                ${result.tags ? `
                    <div class="result-tags">
                        ${result.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                    </div>
                ` : ''}
            </div>
        `).join('');

        resultsList.innerHTML = resultsHtml;
    }

    highlightSearchTerms(text, query) {
        if (!query || !text) return text;
        
        const terms = query.split(' ').filter(term => term.length > 1);
        let highlightedText = text;
        
        terms.forEach(term => {
            const regex = new RegExp(`(${term})`, 'gi');
            highlightedText = highlightedText.replace(regex, '<mark>$1</mark>');
        });
        
        return highlightedText;
    }

    openSearchResult(id, type) {
        // Close search modal
        document.querySelector('.search-modal-overlay')?.remove();
        
        // Navigate to result
        switch (type) {
            case 'meeting':
                window.location.href = `/frontend/meeting.html?id=${id}`;
                break;
            case 'transcript':
                window.location.href = `/frontend/meeting.html?id=${id}#transcript`;
                break;
            case 'action_item':
                window.location.href = `/frontend/meeting.html?id=${id}#actions`;
                break;
            default:
                window.location.href = `/frontend/dashboard.html`;
        }
    }

    addToSearchHistory(query) {
        // Remove if already exists
        this.searchHistory = this.searchHistory.filter(item => item.query !== query);
        
        // Add to beginning
        this.searchHistory.unshift({
            query,
            timestamp: new Date().toISOString()
        });
        
        // Keep only last 10 searches
        this.searchHistory = this.searchHistory.slice(0, 10);
        
        // Save to localStorage
        localStorage.setItem('searchHistory', JSON.stringify(this.searchHistory));
    }

    loadRecentSearches(modal) {
        const recentContainer = modal.querySelector('#recent-searches');
        const popularContainer = modal.querySelector('#popular-searches');
        
        // Recent searches
        if (this.searchHistory.length > 0) {
            const recentHtml = this.searchHistory.slice(0, 5).map(item => `
                <button class="search-suggestion" onclick="searchManager.executeSearch('${item.query}')">
                    <i class="fas fa-history"></i>
                    ${item.query}
                </button>
            `).join('');
            recentContainer.innerHTML = recentHtml;
        } else {
            recentContainer.innerHTML = '<p class="no-suggestions">No recent searches</p>';
        }
        
        // Popular searches
        if (this.popularSearches.length > 0) {
            const popularHtml = this.popularSearches.slice(0, 5).map(item => `
                <button class="search-suggestion" onclick="searchManager.executeSearch('${item.query}')">
                    <i class="fas fa-fire"></i>
                    ${item.query}
                    <span class="search-count">${item.count}</span>
                </button>
            `).join('');
            popularContainer.innerHTML = popularHtml;
        } else {
            popularContainer.innerHTML = '<p class="no-suggestions">No popular searches yet</p>';
        }
    }

    executeSearch(query) {
        const searchInput = document.querySelector('.global-search-input');
        if (searchInput) {
            searchInput.value = query;
            searchInput.dispatchEvent(new Event('input'));
        }
    }

    updateSearchAnalytics(query, resultCount) {
        // Update popular searches
        const existing = this.popularSearches.find(item => item.query === query);
        if (existing) {
            existing.count++;
        } else {
            this.popularSearches.push({ query, count: 1 });
        }
        
        // Sort by count and keep top 10
        this.popularSearches.sort((a, b) => b.count - a.count);
        this.popularSearches = this.popularSearches.slice(0, 10);
        
        // Save to localStorage
        localStorage.setItem('popularSearches', JSON.stringify(this.popularSearches));
        
        // Track search analytics
        this.trackSearchMetrics(query, resultCount);
    }

    trackSearchMetrics(query, resultCount) {
        // Send analytics data (implement as needed)
        console.log('Search Analytics:', {
            query,
            resultCount,
            timestamp: new Date().toISOString(),
            filters: this.searchFilters
        });
    }

    // Quick search for specific content types
    searchMeetings(query) {
        this.searchFilters.type = 'meeting';
        this.openGlobalSearch();
        setTimeout(() => {
            const searchInput = document.querySelector('.global-search-input');
            if (searchInput) {
                searchInput.value = query;
                searchInput.dispatchEvent(new Event('input'));
            }
        }, 100);
    }

    searchTranscripts(query) {
        this.searchFilters.hasTranscript = true;
        this.openGlobalSearch();
        setTimeout(() => {
            const searchInput = document.querySelector('.global-search-input');
            if (searchInput) {
                searchInput.value = query;
                searchInput.dispatchEvent(new Event('input'));
            }
        }, 100);
    }

    clearSearchHistory() {
        this.searchHistory = [];
        localStorage.removeItem('searchHistory');
    }

    clearSearchCache() {
        window.loadingManager?.clearCache('search-');
    }
}

// Create global instance
window.searchManager = new SearchManager();

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SearchManager;
}
