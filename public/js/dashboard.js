// Dashboard JavaScript for Meta Business Analytics

let ageChart = null;
let genderChart = null;
let engagementChart = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Set default date range (last year to show all data)
    const endDate = new Date();
    const startDate = new Date('2024-12-31'); // Start from when data begins
    
    document.getElementById('end_date').value = endDate.toISOString().split('T')[0];
    document.getElementById('start_date').value = startDate.toISOString().split('T')[0];
    
    // Set default platform to 'all'
    document.getElementById('platform').value = 'all';
    
    // Load data after setting defaults
    loadDashboardData();
});

function applyFilters() {
    loadDashboardData();
}

function loadDashboardData() {
    const startDate = document.getElementById('start_date').value;
    const endDate = document.getElementById('end_date').value;
    const platform = document.getElementById('platform').value;
    
    loadFollowerData(startDate, endDate, platform);
    loadDemographicsData(startDate, endDate, platform);
    loadEngagementData(startDate, endDate, platform);
}

function loadFollowerData(startDate, endDate, platform) {
    let url = '/api/followers?';
    if (startDate) url += `start_date=${startDate}&`;
    if (endDate) url += `end_date=${endDate}&`;
    if (platform) url += `platform=${platform}`;
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            updateFollowerStats(data.growth || {});
        })
        .catch(error => {
            console.error('Error loading follower data:', error);
        });
}

function updateFollowerStats(growth) {
    const currentFollowers = growth.last_count || growth.current_followers || 0;
    const totalGrowth = growth.total_growth || 0;
    const growthRate = growth.growth_rate || 0;
    const avgDailyGrowth = growth.average_daily_growth || 0;
    
    document.getElementById('current_followers').textContent = currentFollowers > 0 ? currentFollowers.toLocaleString() : '-';
    document.getElementById('total_growth').textContent = 
        totalGrowth !== 0 ? (totalGrowth > 0 ? `+${totalGrowth.toLocaleString()}` : totalGrowth.toLocaleString()) : '-';
    document.getElementById('growth_rate').textContent = 
        growthRate !== 0 && growthRate !== null && growthRate !== undefined ? `${growthRate.toFixed(2)}%` : '-';
    document.getElementById('avg_daily_growth').textContent = 
        avgDailyGrowth !== 0 && avgDailyGrowth !== null && avgDailyGrowth !== undefined ? `${avgDailyGrowth > 0 ? '+' : ''}${avgDailyGrowth.toFixed(1)}` : '-';
}

function renderFollowerChart(snapshots) {
    const ctx = document.getElementById('followerChart');
    if (!ctx) return;
    
    const canvas = ctx.getContext('2d');
    
    // Handle empty data
    if (!snapshots || snapshots.length === 0) {
        if (followerChart) {
            followerChart.destroy();
        }
        followerChart = new Chart(canvas, {
            type: 'line',
            data: {
                labels: ['Žádná data'],
                datasets: [{
                    label: 'Nahrajte CSV soubory pro zobrazení dat',
                    data: [0],
                    borderColor: '#ccc',
                    backgroundColor: 'rgba(200, 200, 200, 0.1)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' },
                    title: { display: true, text: 'Vývoj počtu followerů v čase - Žádná data' }
                }
            }
        });
        return;
    }
    
    const labels = snapshots.map(s => s.date);
    const followerCounts = snapshots.map(s => s.follower_count || 0);
    const newFollowers = snapshots.map(s => s.new_followers || 0);
    const lostFollowers = snapshots.map(s => s.lost_followers || 0);
    
    if (followerChart) {
        followerChart.destroy();
    }
    
    followerChart = new Chart(canvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Počet followerů',
                    data: followerCounts,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Noví followeri',
                    data: newFollowers,
                    borderColor: '#48bb78',
                    backgroundColor: 'rgba(72, 187, 120, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Ztracení followeri',
                    data: lostFollowers,
                    borderColor: '#f56565',
                    backgroundColor: 'rgba(245, 101, 101, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Vývoj počtu followerů v čase'
                }
            },
            scales: {
                y: {
                    beginAtZero: false
                }
            }
        }
    });
}

function loadDemographicsData(startDate, endDate, platform) {
    let url = '/api/demographics?';
    if (startDate) url += `start_date=${startDate}&`;
    if (endDate) url += `end_date=${endDate}&`;
    if (platform && platform !== 'all') url += `platform=${platform}`;
    
    console.log('Loading demographics with URL:', url); // Debug
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            console.log('Demographics data received:', data); // Debug
            renderAgeChart(data.by_age || []);
            renderGenderChart(data.by_gender || []);
            renderLocationTable(data.by_location || [], data.total || 0);
        })
        .catch(error => {
            console.error('Error loading demographics data:', error);
            renderAgeChart([]);
            renderGenderChart([]);
            renderLocationTable([], 0);
        });
}

function renderAgeChart(ageData) {
    const ctx = document.getElementById('ageChart');
    if (!ctx) return;
    
    const canvas = ctx.getContext('2d');
    
    if (!ageData || ageData.length === 0) {
        if (ageChart) {
            ageChart.destroy();
        }
        ageChart = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: ['Žádná data'],
                datasets: [{
                    label: 'Žádná data',
                    data: [0],
                    backgroundColor: '#ccc'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } }
            }
        });
        return;
    }
    
    const labels = ageData.map(d => d.age_range || 'Neznámé');
    const counts = ageData.map(d => d.count || 0);
    
    if (ageChart) {
        ageChart.destroy();
    }
    
    ageChart = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Počet followerů',
                data: counts,
                backgroundColor: '#667eea',
                borderColor: '#5568d3',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function renderGenderChart(genderData) {
    const ctx = document.getElementById('genderChart');
    if (!ctx) return;
    
    const canvas = ctx.getContext('2d');
    
    if (!genderData || genderData.length === 0) {
        if (genderChart) {
            genderChart.destroy();
        }
        genderChart = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: ['Žádná data'],
                datasets: [{
                    data: [1],
                    backgroundColor: ['#ccc']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } }
            }
        });
        return;
    }
    
    const labels = genderData.map(d => {
        if (d.gender === 'male') return 'Muži';
        if (d.gender === 'female') return 'Ženy';
        return 'Neznámé';
    });
    const counts = genderData.map(d => d.count || 0);
    const colors = ['#667eea', '#764ba2', '#a0aec0'];
    
    if (genderChart) {
        genderChart.destroy();
    }
    
    genderChart = new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: counts,
                backgroundColor: colors.slice(0, counts.length),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function renderLocationTable(locationData, total) {
    const tbody = document.querySelector('#locationTable tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (!locationData || locationData.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="3">Žádná data k zobrazení</td>';
        tbody.appendChild(row);
        return;
    }
    
    locationData.forEach(loc => {
        const percent = total > 0 ? ((loc.count / total) * 100).toFixed(2) : 0;
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${loc.location || 'Neznámé'}</td>
            <td>${(loc.count || 0).toLocaleString()}</td>
            <td>${percent}%</td>
        `;
        tbody.appendChild(row);
    });
}

function loadEngagementData(startDate, endDate, platform) {
    let url = '/api/engagement?';
    if (startDate) url += `start_date=${startDate}&`;
    if (endDate) url += `end_date=${endDate}&`;
    if (platform && platform !== 'all') url += `platform=${platform}`;
    
    console.log('Loading engagement data from:', url); // Debug
    
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Engagement data received:', data); // Debug
            console.log('Metrics count:', data.metrics ? data.metrics.length : 0); // Debug
            updateEngagementStats(data.rates || {});
            renderEngagementChart(data.metrics || []);
        })
        .catch(error => {
            console.error('Error loading engagement data:', error);
            updateEngagementStats({});
            renderEngagementChart([]);
        });
}

function updateEngagementStats(rates) {
    console.log('Engagement rates data:', rates); // Debug
    
    const totalInteractions = rates.total_interactions || 0;
    const avgEngagementRate = rates.average_engagement_rate || 0;
    const totalViews = rates.total_views || 0;
    const avgReach = rates.average_reach || 0;
    
    document.getElementById('total_interactions').textContent = 
        totalInteractions > 0 ? totalInteractions.toLocaleString() : '-';
    document.getElementById('avg_engagement_rate').textContent = 
        avgEngagementRate > 0 ? `${avgEngagementRate.toFixed(2)}%` : '-';
    document.getElementById('total_views').textContent = 
        totalViews > 0 ? totalViews.toLocaleString() : '-';
    document.getElementById('avg_reach').textContent = 
        avgReach > 0 ? avgReach.toLocaleString() : '-';
    
    // Calculate total visits from metrics data
    const totalVisits = rates.total_visits || 0;
    document.getElementById('total_visits').textContent = 
        totalVisits > 0 ? totalVisits.toLocaleString() : '-';
}

function renderEngagementChart(metrics) {
    const ctx = document.getElementById('engagementChart');
    if (!ctx) {
        console.error('engagementChart element not found!');
        return;
    }
    
    const canvas = ctx.getContext('2d');
    console.log('Rendering engagement chart with', metrics ? metrics.length : 0, 'data points');
    
    if (!metrics || metrics.length === 0) {
        if (engagementChart) {
            engagementChart.destroy();
        }
        engagementChart = new Chart(canvas, {
            type: 'line',
            data: {
                labels: ['Žádná data'],
                datasets: [{
                    label: 'Nahrajte CSV soubory pro zobrazení dat',
                    data: [0],
                    borderColor: '#ccc'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top' },
                    title: { display: true, text: 'Engagement metriky v čase - Žádná data' }
                }
            }
        });
        return;
    }
    
    const labels = metrics.map(m => m.date);
    const views = metrics.map(m => m.views || 0);
    const interactions = metrics.map(m => m.interactions || 0);
    const reach = metrics.map(m => m.reach || 0);
    const visits = metrics.map(m => m.visits || 0);
    
    if (engagementChart) {
        engagementChart.destroy();
    }
    
    engagementChart = new Chart(canvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Zobrazení',
                    data: views,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true,
                    yAxisID: 'y'
                },
                {
                    label: 'Interakce',
                    data: interactions,
                    borderColor: '#48bb78',
                    backgroundColor: 'rgba(72, 187, 120, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y1'  // Use secondary Y-axis for interactions
                },
                {
                    label: 'Dosah',
                    data: reach,
                    borderColor: '#f6ad55',
                    backgroundColor: 'rgba(246, 173, 85, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y'
                },
                {
                    label: 'Návštěvy profilu',
                    data: visits,
                    borderColor: '#9f7aea',
                    backgroundColor: 'rgba(159, 122, 234, 0.1)',
                    tension: 0.4,
                    yAxisID: 'y'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Engagement metriky v čase'
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    beginAtZero: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Zobrazení / Dosah'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Interakce'
                    },
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

function exportData(type) {
    const startDate = document.getElementById('start_date').value;
    const endDate = document.getElementById('end_date').value;
    
    let url = `/api/export/csv?type=${type}`;
    if (startDate) url += `&start_date=${startDate}`;
    if (endDate) url += `&end_date=${endDate}`;
    
    window.location.href = url;
}
