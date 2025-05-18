//<script>
//// Function to fetch stock data from your backend
//async function fetchStockData() {
//    const response = await fetch('/api/get-stock-data');
//    const stockData = await response.json();
//    return stockData;
//}
//
//// Function to generate the chart using Chart.js
//function generateChart(stockData) {
//    const ctx = document.getElementById('disp-data').getContext('2d');
//
//    const chart = new Chart(ctx, {
//        type: 'line', // Line chart for stock data
//        data: {
//            labels: stockData.timestamps, // X-axis labels (time)
//            datasets: [
//                {
//                    label: 'EU',
//                    data: stockData.eu, // Y-axis data for EU
//                    borderColor: 'rgba(75, 192, 192, 1)',
//                    fill: false
//                },
//                {
//                    label: 'Wall Street',
//                    data: stockData.wallstreet, // Y-axis data for Wall Street
//                    borderColor: 'rgba(255, 99, 132, 1)',
//                    fill: false
//                },
//                {
//                    label: 'London',
//                    data: stockData.london, // Y-axis data for London
//                    borderColor: 'rgba(54, 162, 235, 1)',
//                    fill: false
//                },
//                {
//                    label: 'China',
//                    data: stockData.china, // Y-axis data for China
//                    borderColor: 'rgba(153, 102, 255, 1)',
//                    fill: false
//                }
//            ]
//        },
//        options: {
//            responsive: true,
//            scales: {
//                x: {
//                    title: {
//                        display: true,
//                        text: 'Time'
//                    }
//                },
//                y: {
//                    title: {
//                        display: true,
//                        text: 'Stock Price'
//                    }
//                }
//            }
//        }
//    });
//}
//
//// Function to update the chart with new data
//async function updateChart() {
//    const stockData = await fetchStockData();
//    generateChart(stockData);
//}
//
//// Update the chart every 30 seconds
//setInterval(updateChart, 30000);
//
//// Initially fetch and render the chart
//updateChart();
//</script>