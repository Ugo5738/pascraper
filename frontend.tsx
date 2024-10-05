// const socket = new WebSocket('ws://localhost:8000/ws/scraper/');

// socket.onopen = function(e) {
//     console.log("WebSocket connection established");
//     socket.send(JSON.stringify({
//         'url': 'https://www.rightmove.co.uk/properties/12345678',
//         'source': 'rightmove'
//     }));
// };

// socket.onmessage = function(event) {
//     const data = JSON.parse(event.data);
//     console.log("Received:", data);
// };