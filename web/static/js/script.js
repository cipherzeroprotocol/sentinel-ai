/**
 * Sentinel AI - Dashboard JavaScript
 * Handles interaction with the dashboard UI
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const addressInput = document.getElementById('addressInput');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const analysisResultsContainer = document.getElementById('analysisResultsContainer');
    const analysisResults = document.getElementById('analysisResults');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const recentAnalysesList = document.getElementById('recentAnalysesList');
    const highRiskEntitiesList = document.getElementById('highRiskEntitiesList');
    
    // Event Listeners
    analyzeBtn.addEventListener('click', handleAnalyzeClick);
    addressInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleAnalyzeClick();
        }
    });
    
    // Initialize dashboard data
    loadRecentAnalyses();
    loadHighRiskEntities();
    
    /**
     * Handle the analyze button click
     */
    function handleAnalyzeClick() {
        const address = addressInput.value.trim();
        if (!address) {
            showError('Please enter a valid Solana address or token');
            return;
        }
        
        // Show loading state
        analysisResultsContainer.style.display = 'block';
        analysisResults.innerHTML = '';
        loadingSpinner.style.display = 'block';
        
        // Get selected analysis type
        const analysisType = document.querySelector('input[name="analysisType"]:checked').value;
        
        // Make API request
        fetchAnalysis(address, analysisType)
            .then(data => {
                loadingSpinner.style.display = 'none';
                displayResults(data);
                
                // Refresh recent analyses
                loadRecentAnalyses();
                
                // Save to local storage
                saveRecentAnalysis(address, data);
            })
            .catch(error => {
                loadingSpinner.style.display = 'none';
                showError('Analysis failed: ' + error.message);
            });
    }
    
    /**
     * Fetch analysis results from the API
     * @param {string} address - The address to analyze
     * @param {string} type - The type of analysis to perform
     * @returns {Promise} - The analysis results
     */
    async function fetchAnalysis(address, type) {
        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ address, type })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Server error');
            }
            
            return await response.json();
        } catch (error) {
            console.error('Analysis error:', error);
            throw error;
        }
    }
    
    /**
     * Display analysis results in the UI
     * @param {Object} data - The analysis results data
     */
    function displayResults(data) {
        // Create results card
        const resultsCard = document.createElement('div');
        resultsCard.classList.add('card', 'mb-4');
        
        // Create summary section
        const cardHeader = document.createElement('div');
        cardHeader.classList.add('card-header', 'd-flex', 'justify-content-between', 'align-items-center');
        
        const headerTitle = document.createElement('h5');
        headerTitle.textContent = 'Analysis Results for ' + truncateAddress(data.address);
        
        const riskBadge = document.createElement('span');
        const riskScore = calculateOverallRiskScore(data.results);
        riskBadge.classList.add('badge', getRiskBadgeColor(riskScore));
        riskBadge.textContent = 'Risk: ' + riskScore + '%';
        
        cardHeader.appendChild(headerTitle);
        cardHeader.appendChild(riskBadge);
        resultsCard.appendChild(cardHeader);
        
        // Create results body
        const cardBody = document.createElement('div');
        cardBody.classList.add('card-body');
        
        // Add View Full Report button
        const reportBtn = document.createElement('a');
        reportBtn.classList.add('btn', 'btn-primary', 'mb-3');
        reportBtn.href = '/report/' + data.report_id;
        reportBtn.textContent = 'View Full Report';
        reportBtn.target = '_blank';
        cardBody.appendChild(reportBtn);
        
        // Create summary results
        const resultsSummary = document.createElement('div');
        resultsSummary.classList.add('row');
        
        // Add result sections based on analysis types
        if (data.results.ico) {
            resultsSummary.appendChild(createResultSection('ICO Analysis', data.results.ico.summary, data.results.ico.risk_score));
        }
        
        if (data.results.money_laundering) {
            resultsSummary.appendChild(createResultSection('Money Laundering', data.results.money_laundering.summary, data.results.money_laundering.risk_score));
        }
        
        if (data.results.rugpull) {
            resultsSummary.appendChild(createResultSection('Rugpull Risk', data.results.rugpull.summary, data.results.rugpull.risk_score));
        }
        
        if (data.results.mixer) {
            resultsSummary.appendChild(createResultSection('Mixer Detection', data.results.mixer.summary, data.results.mixer.risk_score));
        }
        
        if (data.results.dusting) {
            resultsSummary.appendChild(createResultSection('Address Poisoning', data.results.dusting.summary, data.results.dusting.risk_score));
        }
        
        cardBody.appendChild(resultsSummary);
        resultsCard.appendChild(cardBody);
        
        // Add to results container
        analysisResults.innerHTML = '';
        analysisResults.appendChild(resultsCard);
    }
    
    /**
     * Create a result section for a specific analysis type
     * @param {string} title - The section title
     * @param {string} summary - The summary text
     * @param {number} riskScore - The risk score
     * @returns {HTMLElement} - The result section element
     */
    function createResultSection(title, summary, riskScore) {
        const col = document.createElement('div');
        col.classList.add('col-md-6', 'mb-3');
        
        const card = document.createElement('div');
        card.classList.add('card', 'h-100');
        
        const cardHeader = document.createElement('div');
        cardHeader.classList.add('card-header', 'd-flex', 'justify-content-between', 'align-items-center');
        
        const headerTitle = document.createElement('h6');
        headerTitle.textContent = title;
        
        const badge = document.createElement('span');
        badge.classList.add('badge', getRiskBadgeColor(riskScore));
        badge.textContent = riskScore + '%';
        
        cardHeader.appendChild(headerTitle);
        cardHeader.appendChild(badge);
        
        const cardBody = document.createElement('div');
        cardBody.classList.add('card-body');
        cardBody.textContent = summary;
        
        card.appendChild(cardHeader);
        card.appendChild(cardBody);
        col.appendChild(card);
        
        return col;
    }
    
    /**
     * Load recent analyses from local storage
     */
    function loadRecentAnalyses() {
        const recentAnalyses = getRecentAnalyses();
        recentAnalysesList.innerHTML = '';
        
        if (recentAnalyses.length === 0) {
            const emptyItem = document.createElement('li');
            emptyItem.classList.add('list-group-item', 'text-center', 'text-muted');
            emptyItem.textContent = 'No recent analyses';
            recentAnalysesList.appendChild(emptyItem);
            return;
        }
        
        recentAnalyses.forEach(analysis => {
            const item = document.createElement('li');
            item.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-center');
            
            const addressLink = document.createElement('a');
            addressLink.href = '#';
            addressLink.textContent = truncateAddress(analysis.address);
            addressLink.addEventListener('click', (e) => {
                e.preventDefault();
                addressInput.value = analysis.address;
                handleAnalyzeClick();
            });
            
            const riskBadge = document.createElement('span');
            riskBadge.classList.add('badge', getRiskBadgeColor(analysis.riskScore));
            riskBadge.textContent = 'Risk: ' + analysis.riskScore + '%';
            
            item.appendChild(addressLink);
            item.appendChild(riskBadge);
            recentAnalysesList.appendChild(item);
        });
    }
    
    /**
     * Load high risk entities from the server
     */
    function loadHighRiskEntities() {
        // This would normally be an API call, but for now we'll use dummy data
        const highRiskEntities = [
            { address: 'tor1xzb2Zyy1cUxXmyJfR8aNXuWnwHG8AwgaG7UGD4K', type: 'Mixer', riskScore: 92 },
            { address: '5KWGzE5gQW5Kj3pVCv5tELmKb7P7uSbQSdr4VnKWFYgS', type: 'Rugpull Token', riskScore: 88 },
            { address: 'mixerEfg3yXGYZJbhG43RJ2KdMUXbf6s9YGBXnJE9Qj2T', type: 'Mixer', riskScore: 90 },
            { address: '9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin', type: 'Scam Creator', riskScore: 85 },
            { address: 'HRk9D8wLK3c7SRuYJCdmkRZdmPJEg7oaDECuTgcULPp8', type: 'Fraudulent ICO', riskScore: 82 }
        ];
        
        highRiskEntitiesList.innerHTML = '';
        
        highRiskEntities.forEach(entity => {
            const item = document.createElement('li');
            item.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-center');
            
            const leftDiv = document.createElement('div');
            
            const addressLink = document.createElement('a');
            addressLink.href = '#';
            addressLink.textContent = truncateAddress(entity.address);
            addressLink.addEventListener('click', (e) => {
                e.preventDefault();
                addressInput.value = entity.address;
                handleAnalyzeClick();
            });
            
            const typeBadge = document.createElement('span');
            typeBadge.classList.add('badge', 'bg-secondary', 'ms-2');
            typeBadge.textContent = entity.type;
            
            leftDiv.appendChild(addressLink);
            leftDiv.appendChild(typeBadge);
            
            const riskBadge = document.createElement('span');
            riskBadge.classList.add('badge', 'bg-danger');
            riskBadge.textContent = 'Risk: ' + entity.riskScore + '%';
            
            item.appendChild(leftDiv);
            item.appendChild(riskBadge);
            highRiskEntitiesList.appendChild(item);
        });
    }
    
    /**
     * Save a recent analysis to local storage
     * @param {string} address - The analyzed address
     * @param {Object} data - The analysis results
     */
    function saveRecentAnalysis(address, data) {
        const recentAnalyses = getRecentAnalyses();
        
        // Calculate overall risk score
        const riskScore = calculateOverallRiskScore(data.results);
        
        // Add the new analysis
        const newAnalysis = {
            address,
            timestamp: new Date().toISOString(),
            riskScore,
            reportId: data.report_id
        };
        
        // Remove duplicate if exists
        const filteredAnalyses = recentAnalyses.filter(a => a.address !== address);
        
        // Add to beginning and limit to 5
        const updatedAnalyses = [newAnalysis, ...filteredAnalyses].slice(0, 5);
        
        // Save to localStorage
        localStorage.setItem('sentinelRecentAnalyses', JSON.stringify(updatedAnalyses));
    }
    
    /**
     * Get recent analyses from local storage
     * @returns {Array} - Array of recent analyses
     */
    function getRecentAnalyses() {
        const stored = localStorage.getItem('sentinelRecentAnalyses');
        return stored ? JSON.parse(stored) : [];
    }
    
    /**
     * Calculate overall risk score from analysis results
     * @param {Object} results - The analysis results
     * @returns {number} - The overall risk score
     */
    function calculateOverallRiskScore(results) {
        let totalScore = 0;
        let count = 0;
        
        if (results.ico && results.ico.risk_score !== undefined) {
            totalScore += results.ico.risk_score;
            count++;
        }
        
        if (results.money_laundering && results.money_laundering.risk_score !== undefined) {
            totalScore += results.money_laundering.risk_score;
            count++;
        }
        
        if (results.rugpull && results.rugpull.risk_score !== undefined) {
            totalScore += results.rugpull.risk_score;
            count++;
        }
        
        if (results.mixer && results.mixer.risk_score !== undefined) {
            totalScore += results.mixer.risk_score;
            count++;
        }
        
        if (results.dusting && results.dusting.risk_score !== undefined) {
            totalScore += results.dusting.risk_score;
            count++;
        }
        
        return count > 0 ? Math.round(totalScore / count) : 0;
    }
    
    /**
     * Show an error message
     * @param {string} message - The error message
     */
    function showError(message) {
        analysisResultsContainer.style.display = 'block';
        loadingSpinner.style.display = 'none';
        
        const alertDiv = document.createElement('div');
        alertDiv.classList.add('alert', 'alert-danger');
        alertDiv.textContent = message;
        
        analysisResults.innerHTML = '';
        analysisResults.appendChild(alertDiv);
    }
    
    /**
     * Get the appropriate badge color based on risk score
     * @param {number} score - The risk score
     * @returns {string} - The badge color class
     */
    function getRiskBadgeColor(score) {
        if (score >= 70) return 'bg-danger';
        if (score >= 30) return 'bg-warning';
        return 'bg-success';
    }
    
    /**
     * Truncate an address for display
     * @param {string} address - The full address
     * @returns {string} - The truncated address
     */
    function truncateAddress(address) {
        if (!address) return '';
        if (address.length <= 12) return address;
        return address.substring(0, 6) + '...' + address.substring(address.length - 4);
    }
});