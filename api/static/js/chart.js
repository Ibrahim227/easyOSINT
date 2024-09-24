// Create Charts for Blood pressure
const ctx = document.getElementById('disp-data');

new Chart(ctx, {
   type: 'line',
    data: {
      labels: ['Oct, 2023', 'Nov, 2023', 'Dec, 2023', 'Jan, 2024', 'Fev, 2024', 'Mar, 2024'],
      datasets: [{
        label: 'Systolic',
        data: [120, 115, 160, 115, 150, 160],
        borderWidth: 3,
        borderColor: '#C26EB4',
        fill: false
      }, {
        label: 'Diastolic',
        data: [110, 60, 110, 90, 70, 80],
        borderWidth: 3,
        borderColor: '#7E6CAB',
        fill: false
      }
      ]
    },
  options: {
      scales: {
        y: {
          beginAtZero: false
        }
      }
  }
});