/**
 * Analytics Manager
 * Handles meeting analytics, insights, and reporting
 */

class AnalyticsManager {
    constructor() {
        this.analyticsData = {};
        this.insights = [];
        this.charts = new Map();
        this.dateRange = 'month'; // week, month, quarter, year
        
        this.initializeAnalytics();
    }

    initializeAnalytics() {
        this.loadAnalyticsData();
        this.generateInsights();
    }

    async loadAnalyticsData() {
        try {
            const response = await window.loadingManager.fetchWithCache(
                `/api/analytics/dashboard?range=${this.dateRange}`,
                {
                    credentials: 'include',
                    loadingMessage: 'Loading analytics...',
                    cache: true,
                    cacheDuration: 5 * 60 * 1000 // 5 minutes cache
                }
            );

            if (result.success) {
                this.analyticsData = result.data;
                this.generateInsights();
                this.updateAnalyticsDashboard();
            }
        } catch (error) {
            console.error('Error loading analytics:', error);
            window.loadingManager.showToast('Failed to load analytics', 'error');
        }
    }

    generateInsights() {
        this.insights = [];
        
        if (!this.analyticsData.meetings) return;

        const meetings = this.analyticsData.meetings;
        
        // Meeting frequency insights
        this.generateFrequencyInsights(meetings);
        
        // Duration insights
        this.generateDurationInsights(meetings);
        
        // Productivity insights
        this.generateProductivityInsights(meetings);
        
        // Trend insights
        this.generateTrendInsights(meetings);
        
        // Efficiency insights
        this.generateEfficiencyInsights(meetings);
    }

    generateFrequencyInsights(meetings) {
        const totalMeetings = meetings.length;
        const daysInRange = this.getDaysInRange();
        const avgPerDay = totalMeetings / daysInRange;
        
        if (avgPerDay > 3) {
            this.insights.push({
                type: 'warning',
                title: 'High Meeting Frequency',
                message: `You're averaging ${avgPerDay.toFixed(1)} meetings per day. Consider consolidating similar meetings.`,
                action: 'Review meeting schedule',
                priority: 'high'
            });
        } else if (avgPerDay < 0.5) {
            this.insights.push({
                type: 'info',
                title: 'Low Meeting Activity',
                message: `You have ${avgPerDay.toFixed(1)} meetings per day on average. Consider if more collaboration is needed.`,
                action: 'Review collaboration needs',
                priority: 'low'
            });
        }
    }

    generateDurationInsights(meetings) {
        const durations = meetings.map(m => m.duration_minutes).filter(d => d);
        if (durations.length === 0) return;
        
        const avgDuration = durations.reduce((a, b) => a + b, 0) / durations.length;
        const longMeetings = durations.filter(d => d > 60).length;
        const shortMeetings = durations.filter(d => d < 15).length;
        
        if (avgDuration > 45) {
            this.insights.push({
                type: 'warning',
                title: 'Long Meeting Duration',
                message: `Average meeting duration is ${avgDuration.toFixed(0)} minutes. Consider shorter, more focused meetings.`,
                action: 'Optimize meeting length',
                priority: 'medium'
            });
        }
        
        if (longMeetings > meetings.length * 0.3) {
            this.insights.push({
                type: 'warning',
                title: 'Too Many Long Meetings',
                message: `${Math.round(longMeetings / meetings.length * 100)}% of meetings are over 1 hour.`,
                action: 'Break down long meetings',
                priority: 'medium'
            });
        }
    }

    generateProductivityInsights(meetings) {
        const withActionItems = meetings.filter(m => m.action_items && m.action_items.length > 0).length;
        const withDecisions = meetings.filter(m => m.key_decisions && m.key_decisions.length > 0).length;
        
        const actionItemRate = withActionItems / meetings.length;
        const decisionRate = withDecisions / meetings.length;
        
        if (actionItemRate < 0.3) {
            this.insights.push({
                type: 'warning',
                title: 'Low Action Item Generation',
                message: `Only ${Math.round(actionItemRate * 100)}% of meetings generate action items.`,
                action: 'Focus on actionable outcomes',
                priority: 'high'
            });
        }
        
        if (decisionRate < 0.2) {
            this.insights.push({
                type: 'info',
                title: 'Few Decisions Made',
                message: `Only ${Math.round(decisionRate * 100)}% of meetings result in decisions.`,
                action: 'Improve decision-making process',
                priority: 'medium'
            });
        }
    }

    generateTrendInsights(meetings) {
        // Group meetings by week
        const weeklyData = this.groupMeetingsByWeek(meetings);
        const weeks = Object.keys(weeklyData).sort();
        
        if (weeks.length < 2) return;
        
        const recentWeek = weeklyData[weeks[weeks.length - 1]];
        const previousWeek = weeklyData[weeks[weeks.length - 2]];
        
        const change = ((recentWeek.length - previousWeek.length) / previousWeek.length) * 100;
        
        if (change > 50) {
            this.insights.push({
                type: 'warning',
                title: 'Meeting Volume Spike',
                message: `Meeting volume increased by ${change.toFixed(0)}% this week.`,
                action: 'Review meeting necessity',
                priority: 'high'
            });
        } else if (change < -30) {
            this.insights.push({
                type: 'success',
                title: 'Reduced Meeting Load',
                message: `Meeting volume decreased by ${Math.abs(change).toFixed(0)}% this week.`,
                action: 'Maintain efficiency',
                priority: 'low'
            });
        }
    }

    generateEfficiencyInsights(meetings) {
        const processedMeetings = meetings.filter(m => m.status === 'completed');
        const processingTimes = processedMeetings.map(m => {
            const created = new Date(m.created_at);
            const updated = new Date(m.updated_at);
            return (updated - created) / (1000 * 60); // minutes
        });
        
        if (processingTimes.length === 0) return;
        
        const avgProcessingTime = processingTimes.reduce((a, b) => a + b, 0) / processingTimes.length;
        
        if (avgProcessingTime > 30) {
            this.insights.push({
                type: 'info',
                title: 'Processing Time',
                message: `Average processing time is ${avgProcessingTime.toFixed(0)} minutes.`,
                action: 'Consider optimizing workflow',
                priority: 'low'
            });
        }
    }

    createAnalyticsDashboard() {
        const dashboard = document.createElement('div');
        dashboard.className = 'analytics-dashboard';
        dashboard.innerHTML = `
            <div class="analytics-header">
                <h2>Meeting Analytics</h2>
                <div class="analytics-controls">
                    <select id="analytics-range" onchange="analyticsManager.changeRange(this.value)">
                        <option value="week">This Week</option>
                        <option value="month" selected>This Month</option>
                        <option value="quarter">This Quarter</option>
                        <option value="year">This Year</option>
                    </select>
                    <button class="btn secondary" onclick="analyticsManager.exportAnalytics()">
                        <i class="fas fa-download"></i> Export
                    </button>
                </div>
            </div>
            
            <div class="analytics-grid">
                <div class="analytics-card">
                    <div class="card-header">
                        <h3>Meeting Overview</h3>
                        <i class="fas fa-chart-bar"></i>
                    </div>
                    <div class="card-content">
                        <div class="metric-grid">
                            <div class="metric">
                                <span class="metric-value" id="total-meetings">0</span>
                                <span class="metric-label">Total Meetings</span>
                            </div>
                            <div class="metric">
                                <span class="metric-value" id="avg-duration">0m</span>
                                <span class="metric-label">Avg Duration</span>
                            </div>
                            <div class="metric">
                                <span class="metric-value" id="total-hours">0h</span>
                                <span class="metric-label">Total Hours</span>
                            </div>
                            <div class="metric">
                                <span class="metric-value" id="completion-rate">0%</span>
                                <span class="metric-label">Completion Rate</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="analytics-card">
                    <div class="card-header">
                        <h3>Productivity Metrics</h3>
                        <i class="fas fa-tasks"></i>
                    </div>
                    <div class="card-content">
                        <div class="metric-grid">
                            <div class="metric">
                                <span class="metric-value" id="action-items">0</span>
                                <span class="metric-label">Action Items</span>
                            </div>
                            <div class="metric">
                                <span class="metric-value" id="decisions-made">0</span>
                                <span class="metric-label">Decisions Made</span>
                            </div>
                            <div class="metric">
                                <span class="metric-value" id="attendee-avg">0</span>
                                <span class="metric-label">Avg Attendees</span>
                            </div>
                            <div class="metric">
                                <span class="metric-value" id="efficiency-score">0%</span>
                                <span class="metric-label">Efficiency Score</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="analytics-card chart-card">
                    <div class="card-header">
                        <h3>Meeting Trends</h3>
                        <i class="fas fa-chart-line"></i>
                    </div>
                    <div class="card-content">
                        <canvas id="trends-chart" width="400" height="200"></canvas>
                    </div>
                </div>
                
                <div class="analytics-card">
                    <div class="card-header">
                        <h3>Insights & Recommendations</h3>
                        <i class="fas fa-lightbulb"></i>
                    </div>
                    <div class="card-content">
                        <div id="insights-list" class="insights-list"></div>
                    </div>
                </div>
            </div>
        `;
        
        return dashboard;
    }

    updateAnalyticsDashboard() {
        if (!this.analyticsData.meetings) return;
        
        const meetings = this.analyticsData.meetings;
        
        // Update metrics
        this.updateMetric('total-meetings', meetings.length);
        
        const durations = meetings.map(m => m.duration_minutes).filter(d => d);
        const avgDuration = durations.length > 0 ? durations.reduce((a, b) => a + b, 0) / durations.length : 0;
        this.updateMetric('avg-duration', `${Math.round(avgDuration)}m`);
        
        const totalHours = durations.reduce((a, b) => a + b, 0) / 60;
        this.updateMetric('total-hours', `${totalHours.toFixed(1)}h`);
        
        const completedMeetings = meetings.filter(m => m.status === 'completed').length;
        const completionRate = meetings.length > 0 ? (completedMeetings / meetings.length) * 100 : 0;
        this.updateMetric('completion-rate', `${Math.round(completionRate)}%`);
        
        // Productivity metrics
        const totalActionItems = meetings.reduce((sum, m) => sum + (m.action_items ? m.action_items.length : 0), 0);
        this.updateMetric('action-items', totalActionItems);
        
        const totalDecisions = meetings.reduce((sum, m) => sum + (m.key_decisions ? m.key_decisions.length : 0), 0);
        this.updateMetric('decisions-made', totalDecisions);
        
        const avgAttendees = meetings.length > 0 ? 
            meetings.reduce((sum, m) => sum + (m.attendees ? m.attendees.length : 0), 0) / meetings.length : 0;
        this.updateMetric('attendee-avg', Math.round(avgAttendees));
        
        // Calculate efficiency score
        const efficiencyScore = this.calculateEfficiencyScore(meetings);
        this.updateMetric('efficiency-score', `${Math.round(efficiencyScore)}%`);
        
        // Update insights
        this.updateInsightsList();
        
        // Update charts
        this.updateTrendsChart(meetings);
    }

    updateMetric(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    calculateEfficiencyScore(meetings) {
        if (meetings.length === 0) return 0;
        
        let score = 0;
        let factors = 0;
        
        // Factor 1: Action items generation (30%)
        const withActionItems = meetings.filter(m => m.action_items && m.action_items.length > 0).length;
        score += (withActionItems / meetings.length) * 30;
        factors += 30;
        
        // Factor 2: Decision making (25%)
        const withDecisions = meetings.filter(m => m.key_decisions && m.key_decisions.length > 0).length;
        score += (withDecisions / meetings.length) * 25;
        factors += 25;
        
        // Factor 3: Completion rate (25%)
        const completed = meetings.filter(m => m.status === 'completed').length;
        score += (completed / meetings.length) * 25;
        factors += 25;
        
        // Factor 4: Duration efficiency (20%)
        const durations = meetings.map(m => m.duration_minutes).filter(d => d);
        if (durations.length > 0) {
            const avgDuration = durations.reduce((a, b) => a + b, 0) / durations.length;
            const durationScore = Math.max(0, 100 - (avgDuration - 30) * 2); // Optimal around 30 minutes
            score += (durationScore / 100) * 20;
            factors += 20;
        }
        
        return factors > 0 ? (score / factors) * 100 : 0;
    }

    updateInsightsList() {
        const insightsList = document.getElementById('insights-list');
        if (!insightsList) return;
        
        if (this.insights.length === 0) {
            insightsList.innerHTML = '<p class="no-insights">No insights available yet. More data needed.</p>';
            return;
        }
        
        const insightsHtml = this.insights.map(insight => `
            <div class="insight-item ${insight.type}">
                <div class="insight-header">
                    <span class="insight-title">${insight.title}</span>
                    <span class="insight-priority priority-${insight.priority}">${insight.priority}</span>
                </div>
                <p class="insight-message">${insight.message}</p>
                <button class="insight-action btn secondary small">${insight.action}</button>
            </div>
        `).join('');
        
        insightsList.innerHTML = insightsHtml;
    }

    updateTrendsChart(meetings) {
        // Simple chart implementation - in production, use Chart.js or similar
        const canvas = document.getElementById('trends-chart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const weeklyData = this.groupMeetingsByWeek(meetings);
        
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Draw simple line chart
        this.drawSimpleChart(ctx, weeklyData, canvas.width, canvas.height);
    }

    drawSimpleChart(ctx, data, width, height) {
        const weeks = Object.keys(data).sort();
        if (weeks.length === 0) return;
        
        const values = weeks.map(week => data[week].length);
        const maxValue = Math.max(...values, 1);
        
        const padding = 40;
        const chartWidth = width - 2 * padding;
        const chartHeight = height - 2 * padding;
        
        // Draw axes
        ctx.strokeStyle = '#e5e7eb';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, height - padding);
        ctx.lineTo(width - padding, height - padding);
        ctx.stroke();
        
        // Draw data line
        ctx.strokeStyle = '#3b82f6';
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        weeks.forEach((week, index) => {
            const x = padding + (index / (weeks.length - 1)) * chartWidth;
            const y = height - padding - (values[index] / maxValue) * chartHeight;
            
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        
        ctx.stroke();
        
        // Draw data points
        ctx.fillStyle = '#3b82f6';
        weeks.forEach((week, index) => {
            const x = padding + (index / (weeks.length - 1)) * chartWidth;
            const y = height - padding - (values[index] / maxValue) * chartHeight;
            
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, 2 * Math.PI);
            ctx.fill();
        });
    }

    groupMeetingsByWeek(meetings) {
        const grouped = {};
        
        meetings.forEach(meeting => {
            const date = new Date(meeting.created_at);
            const weekStart = new Date(date);
            weekStart.setDate(date.getDate() - date.getDay());
            const weekKey = weekStart.toISOString().split('T')[0];
            
            if (!grouped[weekKey]) {
                grouped[weekKey] = [];
            }
            grouped[weekKey].push(meeting);
        });
        
        return grouped;
    }

    getDaysInRange() {
        switch (this.dateRange) {
            case 'week': return 7;
            case 'month': return 30;
            case 'quarter': return 90;
            case 'year': return 365;
            default: return 30;
        }
    }

    changeRange(range) {
        this.dateRange = range;
        this.loadAnalyticsData();
    }

    async exportAnalytics() {
        try {
            window.loadingManager.showLoading('Exporting analytics...');
            
            const response = await fetch(`/api/analytics/export?range=${this.dateRange}`, {
                credentials: 'include'
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `meeting-analytics-${this.dateRange}-${new Date().toISOString().split('T')[0]}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                window.loadingManager.showToast('Analytics exported successfully', 'success');
            } else {
                throw new Error('Export failed');
            }
        } catch (error) {
            console.error('Export error:', error);
            window.loadingManager.showToast('Failed to export analytics', 'error');
        } finally {
            window.loadingManager.hideLoading();
        }
    }
}

// Create global instance
window.analyticsManager = new AnalyticsManager();

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnalyticsManager;
}
